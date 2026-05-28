from collections.abc import Callable
from datetime import UTC, datetime

from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.models import Notification, NotificationType
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.models import Auction, Deal


def utc_now() -> datetime:
    return datetime.now(UTC)


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
