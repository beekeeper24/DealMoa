from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.models import Notification, NotificationType
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.models import Auction, Deal
from app.modules.products.repository import ProductRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).isoformat()
    return value.astimezone(UTC).isoformat()


@dataclass(frozen=True)
class ScheduledNotificationSummary:
    scanned_auction_count: int
    created_notification_count: int


class NotificationGenerationUseCases:
    def __init__(
        self,
        *,
        favorites_repository: FavoritesRepository,
        notifications_repository: NotificationsRepository,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.favorites_repository = favorites_repository
        self.notifications_repository = notifications_repository
        self.now = now

    def notify_new_deal(self, deal: Deal) -> int:
        user_ids = self.favorites_repository.list_product_favorite_user_ids(deal.product_id)
        return self._create_target_notifications(
            user_ids=user_ids,
            notification_type=NotificationType.NEW_DEAL,
            title="관심 상품에 새 핫딜이 등록되었습니다.",
            body=deal.title,
            target_type="deal",
            target_id=deal.id,
            metadata={
                "productId": deal.product_id,
                "salePrice": deal.sale_price,
                "currency": deal.currency,
            },
        )

    def notify_new_auction(self, auction: Auction) -> int:
        user_ids = self.favorites_repository.list_product_favorite_user_ids(auction.product_id)
        return self._create_target_notifications(
            user_ids=user_ids,
            notification_type=NotificationType.NEW_AUCTION,
            title="관심 상품에 새 경매가 등록되었습니다.",
            body=auction.title,
            target_type="auction",
            target_id=auction.id,
            metadata={
                "productId": auction.product_id,
                "currentPrice": auction.current_price,
                "currency": auction.currency,
            },
        )

    def notify_auction_ending_soon(self, auction: Auction) -> int:
        user_ids = self.favorites_repository.list_auction_favorite_user_ids(auction.id)
        return self._create_target_notifications(
            user_ids=user_ids,
            notification_type=NotificationType.AUCTION_ENDING_SOON,
            title="관심 경매가 곧 종료됩니다.",
            body=auction.title,
            target_type="auction",
            target_id=auction.id,
            metadata={
                "productId": auction.product_id,
                "currentPrice": auction.current_price,
                "currency": auction.currency,
                "endsAt": utc_isoformat(auction.ends_at),
            },
        )

    def _create_target_notifications(
        self,
        *,
        user_ids: list[str],
        notification_type: str,
        title: str,
        body: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, object],
    ) -> int:
        created_count = 0
        now = self.now()
        for user_id in user_ids:
            existing = self.notifications_repository.get_notification_for_target(
                user_id=user_id,
                notification_type=notification_type,
                target_type=target_type,
                target_id=target_id,
            )
            if existing is not None:
                continue
            self.notifications_repository.create_notification(
                Notification(
                    user_id=user_id,
                    type=notification_type,
                    title=title,
                    body=body,
                    target_type=target_type,
                    target_id=target_id,
                    metadata_json=metadata,
                    created_at=now,
                    updated_at=now,
                )
            )
            created_count += 1
        return created_count


class ScheduledNotificationUseCases:
    def __init__(
        self,
        *,
        product_repository: ProductRepository,
        notification_generation: NotificationGenerationUseCases,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.product_repository = product_repository
        self.notification_generation = notification_generation
        self.now = now

    def generate_auction_ending_soon_notifications(
        self,
        *,
        lookahead: timedelta,
        limit: int,
    ) -> ScheduledNotificationSummary:
        starts_at = self.now()
        auctions = self.product_repository.list_active_auctions_ending_between(
            starts_at=starts_at,
            ends_at=starts_at + lookahead,
            limit=limit,
        )
        created_count = 0
        for auction in auctions:
            created_count += self.notification_generation.notify_auction_ending_soon(auction)
        return ScheduledNotificationSummary(
            scanned_auction_count=len(auctions),
            created_notification_count=created_count,
        )
