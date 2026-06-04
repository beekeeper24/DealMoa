from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.discussions import models as discussion_models  # noqa: F401
from app.modules.products import models as product_models  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 6, 1, 2, 0, tzinfo=UTC)


class FakeAuthUseCases:
    def __init__(self, role: str = "USER") -> None:
        self.role = role

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="admin-1" if self.role == "ADMIN" else "user-1",
            email="admin@example.com" if self.role == "ADMIN" else "user@example.com",
            nickname="Admin" if self.role == "ADMIN" else "User",
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
                product_models.Product(
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
        session.commit()
    finally:
        session.close()


def test_discussion_create_requires_auth() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_data(session_factory)

    response = client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "가격 더 내려갈까요?"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_user_can_create_and_public_can_list_visible_discussions() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)

    create_response = client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "가격 더 내려갈까요?"},
        headers={"Authorization": "Bearer access-1"},
    )
    list_response = client.get("/api/v1/products/product-1/discussions")

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "visible"
    assert create_response.json()["userNickname"] == "User"
    assert list_response.status_code == 200
    public_item = list_response.json()["items"][0]
    assert public_item["body"] == "가격 더 내려갈까요?"
    assert public_item["userNickname"] == "User"
    assert "userId" not in public_item
    assert "moderationNote" not in public_item
    assert "riskLevel" not in public_item
    assert "riskScore" not in public_item
    assert "riskReasons" not in public_item


def test_discussion_creation_stores_low_risk_for_clean_comments() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)

    create_response = client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "실사용 후기가 궁금합니다."},
        headers={"Authorization": "Bearer access-1"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "visible"
    assert create_response.json()["riskLevel"] == "low"
    assert create_response.json()["riskScore"] == 0
    assert create_response.json()["riskReasons"] == []


def test_discussion_creation_marks_risky_comments_without_auto_hiding() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)

    create_response = user_client.post(
        "/api/v1/products/product-1/discussions",
        json={
            "body": (
                "카톡으로 문의 주세요. https://spam.example/a "
                "https://spam.example/b 무료바카라"
            )
        },
        headers={"Authorization": "Bearer access-1"},
    )
    public_response = user_client.get("/api/v1/products/product-1/discussions")
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )
    admin_response = admin_client.get(
        "/api/v1/admin/discussions?status=visible",
        headers={"Authorization": "Bearer access-1"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "visible"
    assert create_response.json()["riskLevel"] == "high"
    assert create_response.json()["riskScore"] == 100
    assert set(create_response.json()["riskReasons"]) == {
        "external_contact",
        "repeated_url",
        "blocked_commercial_spam",
    }
    public_item = public_response.json()["items"][0]
    assert "riskLevel" not in public_item
    assert admin_response.json()["items"][0]["riskLevel"] == "high"
    assert "external_contact" in admin_response.json()["items"][0]["riskReasons"]


def test_admin_discussion_queue_orders_risky_comments_before_clean_comments() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    clean_id = user_client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "정상 댓글입니다."},
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    risky_id = user_client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "텔레그램으로 연락 주세요."},
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    response = admin_client.get(
        "/api/v1/admin/discussions?status=visible",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"][:2]] == [risky_id, clean_id]


def test_admin_can_hide_discussion_and_public_list_excludes_hidden_comment() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    comment_id = user_client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "광고성 댓글은 숨겨야 합니다."},
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    hide_response = admin_client.patch(
        f"/api/v1/admin/discussions/{comment_id}",
        json={"action": "hide", "moderationNote": "광고성 내용"},
        headers={"Authorization": "Bearer access-1"},
    )
    public_response = user_client.get("/api/v1/products/product-1/discussions")

    assert hide_response.status_code == 200
    assert hide_response.json()["status"] == "hidden"
    assert hide_response.json()["moderatedByUserId"] == "admin-1"
    assert public_response.json()["items"] == []
    assert latest_audit_action(session_factory) == "discussion_comment.hidden"


def test_admin_discussion_queue_requires_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)

    response = client.get(
        "/api/v1/admin/discussions?status=visible",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_restore_hidden_discussion() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_data(session_factory)
    comment_id = user_client.post(
        "/api/v1/products/product-1/discussions",
        json={"body": "복구 가능한 댓글입니다."},
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )
    admin_client.patch(
        f"/api/v1/admin/discussions/{comment_id}",
        json={"action": "hide", "moderationNote": "임시 숨김"},
        headers={"Authorization": "Bearer access-1"},
    )

    restore_response = admin_client.patch(
        f"/api/v1/admin/discussions/{comment_id}",
        json={"action": "restore", "moderationNote": "문제 없음"},
        headers={"Authorization": "Bearer access-1"},
    )
    list_response = admin_client.get(
        "/api/v1/admin/discussions?status=visible",
        headers={"Authorization": "Bearer access-1"},
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "visible"
    assert list_response.json()["items"][0]["id"] == comment_id
    assert latest_audit_action(session_factory) == "discussion_comment.restored"


def test_discussion_product_not_found_and_comment_not_found_errors() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="ADMIN"))
    seed_data(session_factory)

    product_response = client.get("/api/v1/products/missing-product/discussions")
    comment_response = client.patch(
        "/api/v1/admin/discussions/missing-comment",
        json={"action": "hide", "moderationNote": "missing"},
        headers={"Authorization": "Bearer access-1"},
    )

    assert product_response.status_code == 404
    assert product_response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert comment_response.status_code == 404
    assert comment_response.json()["error"]["code"] == "DISCUSSION_COMMENT_NOT_FOUND"


def latest_audit_action(session_factory: sessionmaker[Session]) -> str:
    session = session_factory()
    try:
        action = session.scalar(
            select(AdminAuditLog.action).order_by(AdminAuditLog.created_at.desc())
        )
        return cast(str, action)
    finally:
        session.close()
