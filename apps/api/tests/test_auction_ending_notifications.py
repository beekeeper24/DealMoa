from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.favorites.models import AuctionFavorite
from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.generation import (
    NotificationGenerationUseCases,
    ScheduledNotificationUseCases,
)
from app.modules.notifications.models import Notification, NotificationType
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.models import Auction, Product
from app.modules.products.repository import ProductRepository
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 29, 10, 0, tzinfo=UTC)


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def add_user(session: Session, user_id: str) -> None:
    session.add(
        User(
            id=user_id,
            email=f"{user_id}@example.com",
            nickname=user_id,
            role="USER",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def add_product(session: Session, product_id: str) -> None:
    session.add(
        Product(
            id=product_id,
            name=f"Product {product_id}",
            brand="Samsung",
            model_name="SM-S260",
            category="smartphone",
            specs=None,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def add_auction(
    session: Session,
    *,
    auction_id: str,
    product_id: str,
    ends_at: datetime | None,
    status: str = "active",
) -> None:
    session.add(
        Auction(
            id=auction_id,
            product_id=product_id,
            title=f"Auction {auction_id}",
            source_url=f"https://example.com/auctions/{auction_id}",
            seller="Example",
            current_price=720000,
            bid_count=3,
            currency="KRW",
            status=status,
            ends_at=ends_at,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def add_auction_favorite(session: Session, *, user_id: str, auction_id: str) -> None:
    session.add(
        AuctionFavorite(
            user_id=user_id,
            auction_id=auction_id,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def make_scheduled_use_cases(session: Session) -> ScheduledNotificationUseCases:
    return ScheduledNotificationUseCases(
        product_repository=ProductRepository(session),
        notification_generation=NotificationGenerationUseCases(
            favorites_repository=FavoritesRepository(session),
            notifications_repository=NotificationsRepository(session),
            now=lambda: NOW,
        ),
        now=lambda: NOW,
    )


def list_notifications(session: Session) -> list[Notification]:
    return list(session.scalars(select(Notification).order_by(Notification.user_id)))


def test_generate_auction_ending_soon_notifications_targets_favorited_active_window_only() -> None:
    session = next(make_session())
    for user_id in ["user-1", "user-2", "user-3", "user-4", "user-5"]:
        add_user(session, user_id)
    for product_id in ["product-1", "product-2", "product-3", "product-4", "product-5"]:
        add_product(session, product_id)
    add_auction(
        session,
        auction_id="auction-ending",
        product_id="product-1",
        ends_at=NOW + timedelta(minutes=30),
    )
    add_auction(
        session,
        auction_id="auction-later",
        product_id="product-2",
        ends_at=NOW + timedelta(hours=2),
    )
    add_auction(
        session,
        auction_id="auction-ended",
        product_id="product-3",
        ends_at=NOW - timedelta(minutes=1),
    )
    add_auction(
        session,
        auction_id="auction-inactive",
        product_id="product-4",
        ends_at=NOW + timedelta(minutes=20),
        status="closed",
    )
    add_auction(session, auction_id="auction-no-end", product_id="product-5", ends_at=None)
    add_auction_favorite(session, user_id="user-1", auction_id="auction-ending")
    add_auction_favorite(session, user_id="user-2", auction_id="auction-ending")
    add_auction_favorite(session, user_id="user-3", auction_id="auction-later")
    add_auction_favorite(session, user_id="user-4", auction_id="auction-ended")
    add_auction_favorite(session, user_id="user-5", auction_id="auction-inactive")

    summary = make_scheduled_use_cases(session).generate_auction_ending_soon_notifications(
        lookahead=timedelta(hours=1),
        limit=100,
    )

    notifications = list_notifications(session)
    assert summary.scanned_auction_count == 1
    assert summary.created_notification_count == 2
    assert [notification.user_id for notification in notifications] == ["user-1", "user-2"]
    assert {notification.type for notification in notifications} == {
        NotificationType.AUCTION_ENDING_SOON
    }
    assert {notification.target_type for notification in notifications} == {"auction"}
    assert {notification.target_id for notification in notifications} == {"auction-ending"}
    assert notifications[0].metadata_json["endsAt"] == (NOW + timedelta(minutes=30)).isoformat()


def test_generate_auction_ending_soon_notifications_is_idempotent_for_duplicate_runs() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_product(session, "product-1")
    add_auction(
        session,
        auction_id="auction-ending",
        product_id="product-1",
        ends_at=NOW + timedelta(minutes=30),
    )
    add_auction_favorite(session, user_id="user-1", auction_id="auction-ending")
    use_cases = make_scheduled_use_cases(session)

    first_summary = use_cases.generate_auction_ending_soon_notifications(
        lookahead=timedelta(hours=1),
        limit=100,
    )
    second_summary = use_cases.generate_auction_ending_soon_notifications(
        lookahead=timedelta(hours=1),
        limit=100,
    )

    notifications = list_notifications(session)
    assert first_summary.created_notification_count == 1
    assert second_summary.created_notification_count == 0
    assert len(notifications) == 1
