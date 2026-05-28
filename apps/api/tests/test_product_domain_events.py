from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.models import DomainEvent
from app.modules.products.models import Product
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 14, 0, tzinfo=UTC)


def make_test_client(
    auth_use_cases: FakeAuthUseCases | None = None,
) -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app()
    if auth_use_cases is not None:
        app.dependency_overrides[get_auth_use_cases] = lambda: auth_use_cases

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


def list_events(session_factory: sessionmaker[Session]) -> list[DomainEvent]:
    session = session_factory()
    try:
        return list(session.scalars(select(DomainEvent).order_by(DomainEvent.created_at)))
    finally:
        session.close()


def seed_product(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add(
            Product(
                id="product-1",
                name="Galaxy S26",
                brand="Samsung",
                model_name="SM-S260",
                category="smartphone",
                specs=None,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
    finally:
        session.close()


class FakeAuthUseCases:
    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="user-1",
            email="user@example.com",
            nickname="Deal User",
            role="USER",
        )


def seed_user(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add(
            User(
                id="user-1",
                email="user@example.com",
                nickname="Deal User",
                role="USER",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
    finally:
        session.close()


def test_create_product_writes_product_updated_outbox_event() -> None:
    client, session_factory = make_test_client()

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Galaxy S26",
            "brand": "Samsung",
            "modelName": "SM-S260",
            "category": "smartphone",
            "specs": {"storage": "256GB"},
        },
    )

    events = list_events(session_factory)
    assert response.status_code == 201
    assert [event.event_type for event in events] == ["product.updated"]
    assert events[0].aggregate_type == "product"
    assert events[0].aggregate_id == response.json()["id"]
    assert events[0].payload_json["productId"] == response.json()["id"]


def test_create_deal_writes_deal_created_outbox_event() -> None:
    client, session_factory = make_test_client()
    seed_product(session_factory)

    response = client.post(
        "/api/v1/products/product-1/deals",
        json={
            "title": "Galaxy S26 launch deal",
            "sourceUrl": "https://example.com/deals/galaxy-s26",
            "salePrice": 1090000,
        },
    )

    events = list_events(session_factory)
    assert response.status_code == 201
    assert [event.event_type for event in events] == ["deal.created"]
    assert events[0].aggregate_type == "deal"
    assert events[0].aggregate_id == response.json()["id"]
    assert events[0].payload_json["productId"] == "product-1"


def test_create_auction_writes_auction_created_outbox_event() -> None:
    client, session_factory = make_test_client()
    seed_product(session_factory)

    response = client.post(
        "/api/v1/products/product-1/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "currentPrice": 720000,
        },
    )

    events = list_events(session_factory)
    assert response.status_code == 201
    assert [event.event_type for event in events] == ["auction.created"]
    assert events[0].aggregate_type == "auction"
    assert events[0].aggregate_id == response.json()["id"]
    assert events[0].payload_json["productId"] == "product-1"


def test_place_auction_bid_writes_auction_bid_placed_outbox_event() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_user(session_factory)
    seed_product(session_factory)
    auction_response = client.post(
        "/api/v1/products/product-1/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "currentPrice": 720000,
        },
    )

    response = client.post(
        f"/api/v1/auctions/{auction_response.json()['id']}/bids",
        json={"amount": 750000},
        headers={"Authorization": "Bearer access-1"},
    )

    events = list_events(session_factory)
    assert response.status_code == 201
    assert [event.event_type for event in events] == [
        "auction.created",
        "auction.bid.placed",
    ]
    bid_event = events[1]
    assert bid_event.aggregate_type == "auction"
    assert bid_event.aggregate_id == auction_response.json()["id"]
    assert bid_event.payload_json["auctionId"] == auction_response.json()["id"]
    assert bid_event.payload_json["userId"] == "user-1"
    assert bid_event.payload_json["amount"] == 750000
    assert bid_event.payload_json["currentPrice"] == 750000
    assert bid_event.payload_json["bidCount"] == 1
