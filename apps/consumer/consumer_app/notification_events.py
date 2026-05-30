from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.generation import NotificationGenerationUseCases
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.repository import ProductRepository
from sqlalchemy.orm import Session


class DomainEventNotificationGenerator:
    def __init__(
        self,
        *,
        product_repository: ProductRepository,
        notification_generation: NotificationGenerationUseCases,
    ) -> None:
        self.product_repository = product_repository
        self.notification_generation = notification_generation

    @classmethod
    def from_session(
        cls,
        *,
        session: Session,
        now: Callable[[], datetime] | None = None,
    ) -> "DomainEventNotificationGenerator":
        notification_generation = NotificationGenerationUseCases(
            favorites_repository=FavoritesRepository(session),
            notifications_repository=NotificationsRepository(session),
        )
        if now is not None:
            notification_generation = NotificationGenerationUseCases(
                favorites_repository=FavoritesRepository(session),
                notifications_repository=NotificationsRepository(session),
                now=now,
            )
        return cls(
            product_repository=ProductRepository(session),
            notification_generation=notification_generation,
        )

    def handle(self, envelope: dict[str, Any]) -> bool:
        event_type = envelope.get("eventType")
        aggregate_id = envelope.get("aggregateId")
        if not isinstance(event_type, str) or not isinstance(aggregate_id, str):
            return False

        if event_type == "deal.created":
            deal = self.product_repository.get_deal(aggregate_id)
            if deal is None:
                return False
            self.notification_generation.notify_new_deal(deal)
            return True

        if event_type == "auction.created":
            auction = self.product_repository.get_auction(aggregate_id)
            if auction is None:
                return False
            self.notification_generation.notify_new_auction(auction)
            return True

        if event_type == "auction.bid.placed":
            auction = self.product_repository.get_auction(aggregate_id)
            if auction is None:
                return False
            payload = envelope.get("payload")
            if not isinstance(payload, dict):
                return True
            new_bidder_user_id = payload.get("userId")
            previous_highest_bidder_user_id = payload.get("previousHighestBidderUserId")
            amount = payload.get("amount")
            if (
                not isinstance(new_bidder_user_id, str)
                or not isinstance(previous_highest_bidder_user_id, str)
                or previous_highest_bidder_user_id == new_bidder_user_id
                or not isinstance(amount, int)
            ):
                return True
            if not self.product_repository.has_auction_bid_from_user(
                auction_id=auction.id,
                user_id=previous_highest_bidder_user_id,
            ):
                return True
            self.notification_generation.notify_auction_outbid(
                auction=auction,
                user_id=previous_highest_bidder_user_id,
                amount=amount,
            )
            return True

        return False
