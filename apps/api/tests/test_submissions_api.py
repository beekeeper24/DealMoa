from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.products.models import Product
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 14, 30, tzinfo=UTC)


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


def submission_payload(
    source_url: str = "https://example.com/deals/galaxy-s26",
) -> dict[str, object]:
    return {
        "offerType": "deal",
        "sourceUrl": source_url,
        "productName": "Galaxy S26",
        "brand": "Samsung",
        "modelName": "SM-S260",
        "category": "smartphone",
        "title": "Galaxy S26 launch deal",
        "seller": "Example Store",
        "originalPrice": 1400000,
        "salePrice": 1090000,
        "currency": "KRW",
        "description": "Launch discount",
    }


def test_create_submission_requires_bearer_token() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_users(session_factory)

    response = client.post("/api/v1/submissions", json=submission_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_submission_rejects_non_http_source_url() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)

    response = client.post(
        "/api/v1/submissions",
        json=submission_payload("javascript:alert(1)"),
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 422


def test_user_can_create_and_list_own_submissions() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)

    create_response = client.post(
        "/api/v1/submissions",
        json=submission_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    list_response = client.get(
        "/api/v1/me/submissions",
        headers={"Authorization": "Bearer access-1"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["offerType"] == "deal"
    assert created["status"] == "pending_review"
    assert created["aiDecision"] == "needs_admin_review"
    assert created["publishedOfferId"] is None
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == created["id"]


def test_duplicate_source_url_returns_existing_submission() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)

    first = client.post(
        "/api/v1/submissions",
        json=submission_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    second = client.post(
        "/api/v1/submissions",
        json=submission_payload(),
        headers={"Authorization": "Bearer access-1"},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_admin_can_list_and_approve_submission() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    submission_response = user_client.post(
        "/api/v1/submissions",
        json=submission_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    submission_id = submission_response.json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    list_response = admin_client.get(
        "/api/v1/admin/submissions?status=pending_review",
        headers={"Authorization": "Bearer access-1"},
    )
    review_response = admin_client.patch(
        f"/api/v1/admin/submissions/{submission_id}",
        json={"action": "approve", "resolutionNote": "approved"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == submission_id
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"
    assert review_response.json()["reviewedByUserId"] == "admin-1"
    assert review_response.json()["publishedProductId"] is not None
    assert review_response.json()["publishedOfferType"] == "deal"
    assert review_response.json()["publishedOfferId"] is not None


def test_admin_can_list_product_matches_and_approve_with_existing_product() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    seed_product(session_factory)
    submission_response = user_client.post(
        "/api/v1/submissions",
        json=submission_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    submission_id = submission_response.json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    matches_response = admin_client.get(
        f"/api/v1/admin/submissions/{submission_id}/product-matches",
        headers={"Authorization": "Bearer access-1"},
    )
    review_response = admin_client.patch(
        f"/api/v1/admin/submissions/{submission_id}",
        json={
            "action": "approve",
            "targetProductId": "product-1",
            "resolutionNote": "기존 상품 연결",
        },
        headers={"Authorization": "Bearer access-1"},
    )

    assert matches_response.status_code == 200
    assert matches_response.json()["items"][0]["productId"] == "product-1"
    assert matches_response.json()["items"][0]["score"] > 0
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"
    assert review_response.json()["publishedProductId"] == "product-1"


def test_admin_submission_queue_requires_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)

    response = client.get(
        "/api/v1/admin/submissions?status=pending_review",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def seed_product(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add(
            Product(
                id="product-1",
                name="Galaxy S26 Ultra",
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
