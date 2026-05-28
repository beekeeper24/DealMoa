from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.auth.models import User
from app.modules.favorites.models import ProductFavorite
from app.modules.notifications.models import Notification, NotificationType
from app.modules.products.models import Product
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 13, 30, tzinfo=UTC)


def make_test_client() -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app()

    def override_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    return TestClient(app), session_factory


def seed_product_favorite(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add_all(
            [
                User(
                    id="user-1",
                    email="user-1@example.com",
                    nickname="user-1",
                    role="USER",
                    created_at=NOW,
                    updated_at=NOW,
                ),
                Product(
                    id="product-1",
                    name="Galaxy S26",
                    brand="Samsung",
                    model_name="SM-S260",
                    category="smartphone",
                    specs=None,
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.add(
            ProductFavorite(
                user_id="user-1",
                product_id="product-1",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
    finally:
        session.close()


def list_notifications(session_factory: sessionmaker[Session]) -> list[Notification]:
    session = session_factory()
    try:
        return list(session.scalars(select(Notification).order_by(Notification.created_at)))
    finally:
        session.close()


def test_creating_deal_generates_notification_for_product_favorite_user() -> None:
    client, session_factory = make_test_client()
    seed_product_favorite(session_factory)

    response = client.post(
        "/api/v1/products/product-1/deals",
        json={
            "title": "Galaxy S26 launch deal",
            "sourceUrl": "https://example.com/deals/galaxy-s26",
            "salePrice": 1090000,
        },
    )

    notifications = list_notifications(session_factory)
    assert response.status_code == 201
    assert len(notifications) == 1
    assert notifications[0].user_id == "user-1"
    assert notifications[0].type == NotificationType.NEW_DEAL
    assert notifications[0].target_type == "deal"
    assert notifications[0].target_id == response.json()["id"]


def test_creating_auction_generates_notification_for_product_favorite_user() -> None:
    client, session_factory = make_test_client()
    seed_product_favorite(session_factory)

    response = client.post(
        "/api/v1/products/product-1/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "currentPrice": 720000,
        },
    )

    notifications = list_notifications(session_factory)
    assert response.status_code == 201
    assert len(notifications) == 1
    assert notifications[0].user_id == "user-1"
    assert notifications[0].type == NotificationType.NEW_AUCTION
    assert notifications[0].target_type == "auction"
    assert notifications[0].target_id == response.json()["id"]
