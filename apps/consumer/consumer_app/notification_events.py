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

        return False
