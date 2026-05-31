from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.evidence import models as evidence_models  # noqa: F401
from app.modules.products import models as product_models  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 6, 1, 0, 30, tzinfo=UTC)


class FakeAuthUseCases:
    def __init__(self, role: str = "USER") -> None:
        self.role = role

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="admin-1" if self.role == "ADMIN" else "user-1",
            email="admin@example.com" if self.role == "ADMIN" else "user@example.com",
            nickname=self.role,
            role=self.role,
        )


def make_test_client(
    auth_use_cases: FakeAuthUseCases | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> tuple[TestClient, sessionmaker[Session]]:
    if session_factory is None:
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


def seed_users(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add_all(
            [
                User(
                    id="user-1",
                    email="user@example.com",
                    nickname="User",
                    role="USER",
                    created_at=NOW,
                    updated_at=NOW,
                ),
                User(
                    id="admin-1",
                    email="admin@example.com",
                    nickname="Admin",
                    role="ADMIN",
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def create_product(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Galaxy S26",
            "brand": "Samsung",
            "modelName": "SM-S260",
            "category": "smartphone",
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def test_offer_creation_records_price_history_snapshots() -> None:
    client, _session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    product = create_product(client)

    deal_response = client.post(
        f"/api/v1/products/{product['id']}/deals",
        json={
            "title": "Galaxy S26 launch deal",
            "sourceUrl": "https://example.com/deals/galaxy-s26",
            "salePrice": 1090000,
            "currency": "KRW",
        },
    )
    auction_response = client.post(
        f"/api/v1/products/{product['id']}/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "currentPrice": 720000,
            "currency": "KRW",
        },
    )
    history_response = client.get(f"/api/v1/products/{product['id']}/price-history")

    assert deal_response.status_code == 201
    assert auction_response.status_code == 201
    assert history_response.status_code == 200
    assert [
        (item["sourceType"], item["sourceId"], item["price"])
        for item in history_response.json()["items"]
    ] == [
        ("auction", auction_response.json()["id"], 720000),
        ("deal", deal_response.json()["id"], 1090000),
    ]


def test_auction_bid_records_price_history_snapshot() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)
    auction = client.post(
        f"/api/v1/products/{product['id']}/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "currentPrice": 720000,
        },
    ).json()

    bid_response = client.post(
        f"/api/v1/auctions/{auction['id']}/bids",
        json={"amount": 730000},
        headers={"Authorization": "Bearer access-1"},
    )
    history_response = client.get(f"/api/v1/products/{product['id']}/price-history")

    assert bid_response.status_code == 201
    assert [item["price"] for item in history_response.json()["items"]] == [730000, 720000]


def test_verified_review_requires_auth_and_admin_approval() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(user_client)

    anonymous_response = user_client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json=verified_review_payload(),
    )
    create_response = user_client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    public_before_approval = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )

    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory,
    )
    list_response = admin_client.get(
        "/api/v1/admin/verified-reviews?status=pending_review",
        headers={"Authorization": "Bearer access-1"},
    )
    review_id = create_response.json()["id"]
    approve_response = admin_client.patch(
        f"/api/v1/admin/verified-reviews/{review_id}",
        json={"action": "approve", "resolutionNote": "영수증 확인"},
        headers={"Authorization": "Bearer access-1"},
    )
    public_after_approval = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )

    assert anonymous_response.status_code == 401
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "pending_review"
    assert create_response.json()["aiDecision"] == "needs_admin_review"
    assert public_before_approval.json()["items"] == []
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == review_id
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"
    public_review = public_after_approval.json()["items"][0]
    assert public_review["id"] == review_id
    assert public_review["title"] == "실구매 기준 만족"
    assert "userId" not in public_review
    assert "proofReference" not in public_review
    assert "aiReason" not in public_review
    assert "resolutionNote" not in public_review


def test_admin_verified_review_queue_requires_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)

    response = client.get(
        "/api/v1/admin/verified-reviews?status=pending_review",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def verified_review_payload() -> dict[str, object]:
    return {
        "rating": 5,
        "title": "실구매 기준 만족",
        "body": "배송과 제품 상태 모두 좋았습니다.",
        "proofType": "receipt",
        "proofReference": "order-123",
    }
