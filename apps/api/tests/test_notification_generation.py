from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.favorites.models import ProductFavorite
from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.generation import NotificationGenerationUseCases
from app.modules.notifications.models import Notification, NotificationType
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.models import Auction, Deal, Product
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 13, 0, tzinfo=UTC)


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


def add_product(session: Session, product_id: str = "product-1") -> Product:
    product = Product(
        id=product_id,
        name="Galaxy S26",
        brand="Samsung",
        model_name="SM-S260",
        category="smartphone",
        specs=None,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(product)
    return product


def add_product_favorite(session: Session, *, user_id: str, product_id: str) -> None:
    session.add(
        ProductFavorite(
            user_id=user_id,
            product_id=product_id,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def make_generation_use_cases(session: Session) -> NotificationGenerationUseCases:
    return NotificationGenerationUseCases(
        favorites_repository=FavoritesRepository(session),
        notifications_repository=NotificationsRepository(session),
        now=lambda: NOW,
    )


def test_notify_new_deal_fans_out_to_product_favorite_users_only() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    add_user(session, "user-3")
    add_product(session, "product-1")
    add_product(session, "product-2")
    add_product_favorite(session, user_id="user-1", product_id="product-1")
    add_product_favorite(session, user_id="user-2", product_id="product-1")
    add_product_favorite(session, user_id="user-3", product_id="product-2")
    deal = Deal(
        id="deal-1",
        product_id="product-1",
        title="Galaxy S26 launch deal",
        source_url="https://example.com/deals/1",
        seller="Example",
        original_price=None,
        sale_price=1090000,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )

    created_count = make_generation_use_cases(session).notify_new_deal(deal)
    notifications = list(session.scalars(select(Notification).order_by(Notification.user_id)))

    assert created_count == 2
    assert [notification.user_id for notification in notifications] == ["user-1", "user-2"]
    assert {notification.type for notification in notifications} == {NotificationType.NEW_DEAL}
    assert {notification.target_type for notification in notifications} == {"deal"}
    assert {notification.target_id for notification in notifications} == {"deal-1"}


def test_notify_new_auction_is_idempotent_for_same_target() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_product(session, "product-1")
    add_product_favorite(session, user_id="user-1", product_id="product-1")
    auction = Auction(
        id="auction-1",
        product_id="product-1",
        title="Galaxy S26 sealed auction",
        source_url="https://example.com/auctions/1",
        seller="Example",
        current_price=720000,
        bid_count=3,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )
    use_cases = make_generation_use_cases(session)

    first_count = use_cases.notify_new_auction(auction)
    second_count = use_cases.notify_new_auction(auction)
    notifications = list(session.scalars(select(Notification)))

    assert first_count == 1
    assert second_count == 0
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.NEW_AUCTION
    assert notifications[0].target_type == "auction"
    assert notifications[0].target_id == "auction-1"
