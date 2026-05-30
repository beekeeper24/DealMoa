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
from app.modules.products.models import Auction, Deal, Product
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 3, 40, tzinfo=UTC)


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


def seed_data(session_factory: sessionmaker[Session]) -> None:
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
                Deal(
                    id="deal-1",
                    product_id="product-1",
                    title="Galaxy S26 launch deal",
                    source_url="https://example.com/deals/galaxy-s26",
                    seller="Example",
                    original_price=None,
                    sale_price=1090000,
                    currency="KRW",
                    status="active",
                    created_at=NOW,
                    updated_at=NOW,
                ),
                Auction(
                    id="auction-1",
                    product_id="product-1",
                    title="Galaxy S26 sealed auction",
                    source_url="https://example.com/auctions/galaxy-s26",
                    seller="Example",
                    current_price=720000,
                    bid_count=3,
                    currency="KRW",
                    status="active",
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def test_report_create_requires_bearer_token() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_data(session_factory)

    response = client.post(
        "/api/v1/reports/deals/deal-1",
        json={"reasonCode": "fraud", "description": None},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_user_can_report_deal_and_auction() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_data(session_factory)

    deal_response = client.post(
        "/api/v1/reports/deals/deal-1",
        json={"reasonCode": "fraud", "description": "Suspicious"},
        headers={"Authorization": "Bearer access-1"},
    )
    auction_response = client.post(
        "/api/v1/reports/auctions/auction-1",
        json={"reasonCode": "broken_link", "description": None},
        headers={"Authorization": "Bearer access-1"},
    )

    assert deal_response.status_code == 201
    assert deal_response.json()["targetType"] == "deal"
    assert deal_response.json()["targetId"] == "deal-1"
    assert deal_response.json()["reasonCode"] == "fraud"
    assert deal_response.json()["status"] == "open"
    assert auction_response.status_code == 201
    assert auction_response.json()["targetType"] == "auction"
    assert auction_response.json()["targetId"] == "auction-1"


def test_admin_report_queue_requires_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)

    response = client.get(
        "/api/v1/admin/reports",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_list_and_review_reports() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    report_response = user_client.post(
        "/api/v1/reports/deals/deal-1",
        json={"reasonCode": "fraud", "description": "Suspicious"},
        headers={"Authorization": "Bearer access-1"},
    )
    report_id = report_response.json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    list_response = admin_client.get(
        "/api/v1/admin/reports?status=open&limit=20",
        headers={"Authorization": "Bearer access-1"},
    )
    review_response = admin_client.patch(
        f"/api/v1/admin/reports/{report_id}",
        json={"status": "resolved", "resolutionNote": "status changed"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == report_id
    assert list_response.json()["items"][0]["status"] == "open"
    assert list_response.json()["nextCursor"] is None
    assert review_response.status_code == 200
    assert review_response.json()["id"] == report_id
    assert review_response.json()["status"] == "resolved"
    assert review_response.json()["reviewedByUserId"] == "admin-1"
    assert review_response.json()["resolutionNote"] == "status changed"


def test_admin_can_review_report_and_change_target_status() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    report_response = user_client.post(
        "/api/v1/reports/deals/deal-1",
        json={"reasonCode": "fraud", "description": "Suspicious"},
        headers={"Authorization": "Bearer access-1"},
    )
    report_id = report_response.json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    review_response = admin_client.patch(
        f"/api/v1/admin/reports/{report_id}",
        json={
            "status": "resolved",
            "resolutionNote": "confirmed fraudulent listing",
            "targetStatus": "rejected",
        },
        headers={"Authorization": "Bearer access-1"},
    )

    session = session_factory()
    try:
        deal = session.get(Deal, "deal-1")
        event = session.query(DomainEvent).one()
    finally:
        session.close()
    assert deal is not None
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "resolved"
    assert deal.status == "rejected"
    assert event.event_type == "deal.status.changed"
    assert event.payload_json["newStatus"] == "rejected"


def test_admin_report_review_rejects_unknown_target_status() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    report_response = user_client.post(
        "/api/v1/reports/deals/deal-1",
        json={"reasonCode": "fraud", "description": "Suspicious"},
        headers={"Authorization": "Bearer access-1"},
    )
    report_id = report_response.json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    response = admin_client.patch(
        f"/api/v1/admin/reports/{report_id}",
        json={
            "status": "resolved",
            "resolutionNote": "bad value",
            "targetStatus": "shadow_hidden",
        },
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
