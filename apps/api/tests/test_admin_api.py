from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.products.models import Auction, Deal, Product
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 2, 45, tzinfo=UTC)


class FakeAuthUseCases:
    def __init__(self, role: str = "ADMIN") -> None:
        self.role = role

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="admin-1",
            email="admin@example.com",
            nickname="Admin",
            role=self.role,
        )


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


def seed_offer_data(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add_all(
            [
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
                    status="pending",
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
                    status="pending",
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def get_audit_logs(session_factory: sessionmaker[Session]) -> list[AdminAuditLog]:
    session = session_factory()
    try:
        return list(session.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at)))
    finally:
        session.close()


def test_admin_status_update_requires_bearer_token() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_offer_data(session_factory)

    response = client.patch(
        "/api/v1/admin/deals/deal-1/status",
        json={"status": "active", "reason": "approved"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_status_update_requires_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_offer_data(session_factory)

    response = client.patch(
        "/api/v1/admin/deals/deal-1/status",
        json={"status": "active", "reason": "approved"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_update_deal_status() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_offer_data(session_factory)

    response = client.patch(
        "/api/v1/admin/deals/deal-1/status",
        json={"status": "active", "reason": "approved"},
        headers={"Authorization": "Bearer access-1"},
    )

    audit_logs = get_audit_logs(session_factory)
    assert response.status_code == 200
    assert response.json()["targetType"] == "deal"
    assert response.json()["targetId"] == "deal-1"
    assert response.json()["previousStatus"] == "pending"
    assert response.json()["status"] == "active"
    assert response.json()["auditLogId"] == audit_logs[0].id
    assert audit_logs[0].reason == "approved"


def test_admin_can_update_auction_status() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_offer_data(session_factory)

    response = client.patch(
        "/api/v1/admin/auctions/auction-1/status",
        json={"status": "rejected", "reason": "duplicate listing"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json()["targetType"] == "auction"
    assert response.json()["targetId"] == "auction-1"
    assert response.json()["previousStatus"] == "pending"
    assert response.json()["status"] == "rejected"


def test_admin_status_update_rejects_unknown_status() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_offer_data(session_factory)

    response = client.patch(
        "/api/v1/admin/deals/deal-1/status",
        json={"status": "shadow_hidden", "reason": "bad value"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
