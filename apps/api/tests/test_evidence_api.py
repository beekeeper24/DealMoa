from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.ai_review.models import AIReviewUsageEvent
from app.modules.ai_review.provider import AIReviewResult
from app.modules.ai_review.rate_limits import AIReviewRateLimiter, AIReviewUsageRepository
from app.modules.auth.models import User
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.evidence import models as evidence_models  # noqa: F401
from app.modules.evidence.models import VerifiedReview
from app.modules.evidence.repository import EvidenceRepository
from app.modules.evidence.schemas import VerifiedReviewCreateRequest
from app.modules.evidence.use_cases import EvidenceUseCases
from app.modules.products import models as product_models  # noqa: F401
from app.modules.products.repository import ProductRepository
from app.modules.submissions.schemas import SubmissionCreateRequest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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


def test_verified_review_requires_auth_and_auto_publishes() -> None:
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
    public_after_create = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )

    assert anonymous_response.status_code == 401
    assert create_response.status_code == 201
    review_id = create_response.json()["id"]
    assert create_response.json()["status"] == "approved"
    assert create_response.json()["aiDecision"] is None
    assert create_response.json()["aiReason"] is None
    assert create_response.json()["aiReviewedAt"] is None
    public_review = public_after_create.json()["items"][0]
    assert public_review["id"] == review_id
    assert public_review["title"] == "실구매 기준 만족"
    assert "userId" not in public_review
    assert "proofReference" not in public_review
    assert "aiReason" not in public_review
    assert "resolutionNote" not in public_review
    assert "riskLevel" not in public_review
    assert "riskScore" not in public_review
    assert "riskReasons" not in public_review


def test_verified_review_creation_stores_low_risk_for_clean_reviews() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(user_client)

    create_response = user_client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )
    admin_response = admin_client.get(
        "/api/v1/admin/verified-reviews?status=approved",
        headers={"Authorization": "Bearer access-1"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "approved"
    assert "riskLevel" not in create_response.json()
    assert admin_response.status_code == 200
    admin_item = admin_response.json()["items"][0]
    assert admin_item["riskLevel"] == "low"
    assert admin_item["riskScore"] == 0
    assert admin_item["riskReasons"] == []


def test_verified_review_risk_signals_do_not_auto_hide_reviews() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(user_client)
    risky_response = user_client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json={
            **verified_review_payload(),
            "title": "카톡 문의 가능한 후기",
            "body": (
                "카톡으로 문의 주세요. https://spam.example/a "
                "https://spam.example/b 무료바카라"
            ),
        },
        headers={"Authorization": "Bearer access-1"},
    )
    public_response = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )
    admin_response = admin_client.get(
        "/api/v1/admin/verified-reviews?status=approved",
        headers={"Authorization": "Bearer access-1"},
    )

    assert risky_response.status_code == 201
    assert risky_response.json()["status"] == "approved"
    assert {item["id"] for item in public_response.json()["items"]} == {
        risky_response.json()["id"],
    }
    risky_admin_item = next(
        item for item in admin_response.json()["items"] if item["id"] == risky_response.json()["id"]
    )
    assert risky_admin_item["status"] == "approved"
    assert risky_admin_item["riskLevel"] == "high"
    assert risky_admin_item["riskScore"] == 100
    assert set(risky_admin_item["riskReasons"]) == {
        "external_contact",
        "repeated_url",
        "blocked_commercial_spam",
    }
    public_risky_item = next(
        item
        for item in public_response.json()["items"]
        if item["id"] == risky_response.json()["id"]
    )
    assert "riskLevel" not in public_risky_item
    assert "riskScore" not in public_risky_item
    assert "riskReasons" not in public_risky_item


def test_admin_verified_review_queue_orders_risky_reviews_before_clean_reviews() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    clean_product = create_product(user_client)
    risky_product = user_client.post(
        "/api/v1/products",
        json={
            "name": "iPhone 18",
            "brand": "Apple",
            "modelName": "A-18",
            "category": "smartphone",
        },
    ).json()
    clean_id = user_client.post(
        f"/api/v1/products/{clean_product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    risky_id = user_client.post(
        f"/api/v1/products/{risky_product['id']}/verified-reviews",
        json={
            **verified_review_payload(),
            "proofReference": "order-456",
            "title": "텔레그램 문의 후기",
            "body": "텔레그램으로 연락 주세요.",
        },
        headers={"Authorization": "Bearer access-1"},
    ).json()["id"]
    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory=session_factory,
    )

    response = admin_client.get(
        "/api/v1/admin/verified-reviews?status=approved",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"][:2]] == [risky_id, clean_id]


def test_verified_review_does_not_call_ai_provider_for_auto_publish() -> None:
    class RaisingReviewProvider:
        def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
            raise AssertionError("submission provider should not be called")

        def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
            raise AssertionError("verified review provider should not be called")

    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)
    session = session_factory()
    try:
        use_cases = EvidenceUseCases(
            evidence_repository=EvidenceRepository(session),
            product_repository=ProductRepository(session),
            ai_review_provider=RaisingReviewProvider(),
            now=lambda: NOW,
        )

        review = use_cases.create_verified_review(
            actor=AuthenticatedUser(
                id="user-1",
                email="user@example.com",
                nickname="User",
                role="USER",
            ),
            product_id=str(product["id"]),
            request=VerifiedReviewCreateRequest.model_validate(verified_review_payload()),
        )
    finally:
        session.close()

    assert review.status == "approved"
    assert review.ai_decision is None
    assert review.ai_reason is None
    assert review.ai_reviewed_at is None


def test_verified_review_auto_publish_does_not_consume_ai_review_quota() -> None:
    class CountingReviewProvider:
        calls = 0

        def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
            raise AssertionError("submission provider should not be called")

        def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
            self.calls += 1
            return AIReviewResult(
                decision="needs_admin_review",
                reason="provider called",
            )

    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)
    second_product = client.post(
        "/api/v1/products",
        json={
            "name": "iPhone 18",
            "brand": "Apple",
            "modelName": "A-18",
            "category": "smartphone",
        },
    ).json()
    session = session_factory()
    try:
        provider = CountingReviewProvider()
        use_cases = EvidenceUseCases(
            evidence_repository=EvidenceRepository(session),
            product_repository=ProductRepository(session),
            ai_review_provider=provider,
            ai_review_rate_limiter=AIReviewRateLimiter(
                repository=AIReviewUsageRepository(session),
                window_limit=1,
                window_hours=24,
            ),
            now=lambda: NOW,
        )
        actor = AuthenticatedUser(
            id="user-1",
            email="user@example.com",
            nickname="User",
            role="USER",
        )

        first = use_cases.create_verified_review(
            actor=actor,
            product_id=str(product["id"]),
            request=VerifiedReviewCreateRequest.model_validate(verified_review_payload()),
        )
        second = use_cases.create_verified_review(
            actor=actor,
            product_id=str(second_product["id"]),
            request=VerifiedReviewCreateRequest.model_validate(
                {
                    **verified_review_payload(),
                    "proofReference": "order-456",
                    "title": "두 번째 실구매 후기",
                }
            ),
        )

        usage_events = list(session.scalars(select(AIReviewUsageEvent)))
    finally:
        session.close()

    assert first.status == "approved"
    assert second.status == "approved"
    assert provider.calls == 0
    assert usage_events == []


def test_verified_review_requires_purchase_proof_reference() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)

    response = client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json={**verified_review_payload(), "proofReference": "   "},
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 422


def test_verified_review_rejects_same_user_product_duplicate() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)
    first_response = client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    )

    duplicate_response = client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json={
            **verified_review_payload(),
            "proofReference": "order-456",
            "title": "두 번째 실구매 후기",
        },
        headers={"Authorization": "Bearer access-1"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "VERIFIED_REVIEW_ALREADY_EXISTS"
    assert duplicate_response.json()["error"]["details"] == {
        "productId": product["id"],
        "userId": "user-1",
    }


def test_verified_review_rejects_reused_proof_reference() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    first_product = create_product(client)
    second_product = client.post(
        "/api/v1/products",
        json={
            "name": "iPhone 18",
            "brand": "Apple",
            "modelName": "A-18",
            "category": "smartphone",
        },
    ).json()
    first_response = client.post(
        f"/api/v1/products/{first_product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    )

    duplicate_response = client.post(
        f"/api/v1/products/{second_product['id']}/verified-reviews",
        json={
            **verified_review_payload(),
            "title": "다른 상품 후기",
        },
        headers={"Authorization": "Bearer access-1"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "VERIFIED_REVIEW_PROOF_ALREADY_USED"
    assert duplicate_response.json()["error"]["details"] == {
        "proofReference": "order-123",
    }


def test_admin_can_hide_and_restore_auto_published_verified_review() -> None:
    user_client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(user_client)
    create_response = user_client.post(
        f"/api/v1/products/{product['id']}/verified-reviews",
        json=verified_review_payload(),
        headers={"Authorization": "Bearer access-1"},
    )
    review_id = create_response.json()["id"]
    assert user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    ).json()["items"][0]["id"] == review_id

    admin_client, _session_factory = make_test_client(
        FakeAuthUseCases(role="ADMIN"),
        session_factory,
    )
    hide_response = admin_client.patch(
        f"/api/v1/admin/verified-reviews/{review_id}",
        json={"action": "hide", "resolutionNote": "신고 확인"},
        headers={"Authorization": "Bearer access-1"},
    )
    public_after_hide = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )
    restore_response = admin_client.patch(
        f"/api/v1/admin/verified-reviews/{review_id}",
        json={"action": "restore", "resolutionNote": "오해 소명"},
        headers={"Authorization": "Bearer access-1"},
    )
    public_after_restore = user_client.get(
        f"/api/v1/products/{product['id']}/verified-reviews"
    )

    assert hide_response.status_code == 200
    assert hide_response.json()["status"] == "hidden"
    assert public_after_hide.json()["items"] == []
    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "approved"
    assert public_after_restore.json()["items"][0]["id"] == review_id


def test_my_verified_reviews_list_only_current_user_reviews_with_cursor() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_users(session_factory)
    product = create_product(client)
    second_product = client.post(
        "/api/v1/products",
        json={
            "name": "iPhone 18",
            "brand": "Apple",
            "modelName": "A-18",
            "category": "smartphone",
        },
    ).json()
    session = session_factory()
    try:
        session.add(
            User(
                id="user-2",
                email="other@example.com",
                nickname="Other",
                role="USER",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add_all(
            [
                VerifiedReview(
                    id="review-user-1-old",
                    product_id=str(product["id"]),
                    user_id="user-1",
                    rating=4,
                    title="첫 번째 실구매 후기",
                    body="첫 번째 후기입니다.",
                    proof_type="receipt",
                    proof_reference="order-old",
                    status="rejected",
                    ai_decision="needs_admin_review",
                    ai_reason="mock review passed",
                    ai_reviewed_at=NOW,
                    reviewed_by_user_id="admin-1",
                    resolution_note="영수증 식별 불가",
                    resolved_at=NOW,
                    created_at=datetime(2026, 6, 1, 0, 10, tzinfo=UTC),
                    updated_at=datetime(2026, 6, 1, 0, 20, tzinfo=UTC),
                ),
                VerifiedReview(
                    id="review-user-1-new",
                    product_id=str(second_product["id"]),
                    user_id="user-1",
                    rating=5,
                    title="두 번째 실구매 후기",
                    body="두 번째 후기입니다.",
                    proof_type="receipt",
                    proof_reference="order-new",
                    status="approved",
                    ai_decision="needs_admin_review",
                    ai_reason="mock review passed",
                    ai_reviewed_at=NOW,
                    reviewed_by_user_id="admin-1",
                    resolution_note="영수증 확인",
                    resolved_at=NOW,
                    created_at=datetime(2026, 6, 1, 0, 30, tzinfo=UTC),
                    updated_at=datetime(2026, 6, 1, 0, 40, tzinfo=UTC),
                ),
                VerifiedReview(
                    id="review-user-2-newer",
                    product_id=str(product["id"]),
                    user_id="user-2",
                    rating=1,
                    title="다른 사용자 후기",
                    body="다른 사용자 후기입니다.",
                    proof_type="receipt",
                    proof_reference="other-order",
                    status="pending_review",
                    ai_decision="needs_admin_review",
                    ai_reason="other review",
                    ai_reviewed_at=NOW,
                    reviewed_by_user_id=None,
                    resolution_note=None,
                    resolved_at=None,
                    created_at=datetime(2026, 6, 1, 0, 50, tzinfo=UTC),
                    updated_at=datetime(2026, 6, 1, 0, 50, tzinfo=UTC),
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    first_page = client.get(
        "/api/v1/me/verified-reviews?limit=1",
        headers={"Authorization": "Bearer access-1"},
    )
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert [item["id"] for item in first_body["items"]] == ["review-user-1-new"]
    assert first_body["items"][0]["proofReference"] == "order-new"
    assert first_body["items"][0]["aiReason"] == "mock review passed"
    assert first_body["items"][0]["resolutionNote"] == "영수증 확인"
    assert first_body["items"][0]["status"] == "approved"
    assert first_body["nextCursor"] == "review-user-1-new"

    second_page = client.get(
        f"/api/v1/me/verified-reviews?limit=1&cursor={first_body['nextCursor']}",
        headers={"Authorization": "Bearer access-1"},
    )
    assert second_page.status_code == 200
    second_body = second_page.json()
    assert [item["id"] for item in second_body["items"]] == ["review-user-1-old"]
    assert second_body["items"][0]["proofReference"] == "order-old"
    assert second_body["nextCursor"] is None


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
