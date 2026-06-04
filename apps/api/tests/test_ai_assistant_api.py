from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any, cast

from app.core.pagination import CursorPage
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.ai_assistant.provider import PurchaseCheckExplanation
from app.modules.ai_assistant.router import get_ai_assistant_use_cases
from app.modules.ai_assistant.schemas import SearchIntent, SearchIntentFilters
from app.modules.ai_assistant.use_cases import AiAssistantUseCases
from app.modules.auth.models import User
from app.modules.evidence.models import PriceHistorySnapshot, VerifiedReview
from app.modules.evidence.repository import EvidenceRepository
from app.modules.products.models import Deal, Product
from app.modules.products.repository import ProductRepository
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 6, 1, 1, 0, tzinfo=UTC)


class FakeSearchUseCases:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int, str | None]] = []

    def search_products(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("products", query, limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "product-1",
                    "name": "Galaxy S26",
                    "brand": "Samsung",
                    "modelName": "SM-S260",
                    "category": "smartphone",
                    "specsText": "storage 256GB",
                    "createdAt": "2026-06-01T00:00:00Z",
                    "updatedAt": "2026-06-01T00:00:00Z",
                    "score": 12.5,
                }
            ],
            next_cursor=None,
        )

    def search_deals(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("deals", query, limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "deal-1",
                    "productId": "product-1",
                    "title": "Galaxy S26 launch deal",
                    "sourceUrl": "https://example.com/deals/galaxy-s26",
                    "seller": "Example Store",
                    "originalPrice": 1400000,
                    "salePrice": 990000,
                    "favoriteCount": 4,
                    "currency": "KRW",
                    "status": "active",
                    "trustScore": 10,
                    "startedAt": None,
                    "endedAt": None,
                    "createdAt": "2026-06-01T00:00:00Z",
                    "updatedAt": "2026-06-01T00:00:00Z",
                    "score": 9.0,
                }
            ],
            next_cursor=None,
        )

    def search_auctions(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("auctions", query, limit, cursor))
        return CursorPage(items=[], next_cursor=None)


class ProductsOnlyAssistantProvider:
    def parse_search_intent(self, query: str) -> SearchIntent:
        return SearchIntent(
            query=query,
            normalizedQuery="provider parsed products only",
            targetTypes=["products"],
            filters=SearchIntentFilters(category="smartphone", maxPrice=900000),
        )

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Any],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        return PurchaseCheckExplanation(
            recommendation="watch",
            confidence=0.51,
            summary="provider purchase explanation",
        )


class FixedPurchaseAssistantProvider(ProductsOnlyAssistantProvider):
    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Any],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        return PurchaseCheckExplanation(
            recommendation="avoid",
            confidence=0.82,
            summary="AI provider says the current price is too high.",
        )


def make_sqlite_client() -> tuple[TestClient, sessionmaker[Session]]:
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


def test_ai_search_extracts_intent_and_uses_allowed_targets() -> None:
    search_use_cases = FakeSearchUseCases()
    use_cases = AiAssistantUseCases(
        search_use_cases=search_use_cases,
        product_repository=cast(Any, None),
        evidence_repository=cast(Any, None),
    )
    app = create_app()
    app.dependency_overrides[get_ai_assistant_use_cases] = lambda: use_cases
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/search",
        json={"query": "갤럭시 100만원 이하 핫딜 찾아줘", "limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["normalizedQuery"] == "갤럭시 100만원 이하 핫딜 찾아줘"
    assert body["intent"]["targetTypes"] == ["deals"]
    assert body["intent"]["filters"] == {"maxPrice": 1000000}
    assert body["deals"]["items"][0]["id"] == "deal-1"
    assert body["summary"] == "핫딜 중심으로 1개 후보를 찾았습니다."
    assert search_use_cases.calls == [("deals", "갤럭시 100만원 이하 핫딜 찾아줘", 3, None)]


def test_ai_search_uses_injected_provider_intent_for_allowed_targets() -> None:
    search_use_cases = FakeSearchUseCases()
    use_cases = AiAssistantUseCases(
        search_use_cases=search_use_cases,
        product_repository=cast(Any, None),
        evidence_repository=cast(Any, None),
        ai_assistant_provider=ProductsOnlyAssistantProvider(),
    )
    app = create_app()
    app.dependency_overrides[get_ai_assistant_use_cases] = lambda: use_cases
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/search",
        json={"query": "갤럭시랑 경매랑 핫딜 다 찾아줘", "limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["normalizedQuery"] == "provider parsed products only"
    assert body["intent"]["targetTypes"] == ["products"]
    assert body["products"]["items"][0]["id"] == "product-1"
    assert body["deals"]["items"] == []
    assert body["auctions"]["items"] == []
    assert search_use_cases.calls == [
        ("products", "갤럭시랑 경매랑 핫딜 다 찾아줘", 3, None)
    ]


def test_purchase_check_uses_price_history_and_public_verified_reviews() -> None:
    client, session_factory = make_sqlite_client()
    seed_purchase_check_data(session_factory)

    response = client.get("/api/v1/ai/products/product-1/purchase-check")

    assert response.status_code == 200
    body = response.json()
    assert body["productId"] == "product-1"
    assert body["recommendation"] == "buy"
    assert body["confidence"] >= 0.7
    assert "가격 이력" in body["summary"]
    assert body["evidence"][0]["type"] == "current_deal"
    assert any(item["type"] == "verified_review" for item in body["evidence"])
    assert "proofReference" not in str(body)
    assert "aiReason" not in str(body)
    assert "resolutionNote" not in str(body)


def test_purchase_check_uses_provider_explanation_but_server_built_evidence() -> None:
    client, session_factory = make_sqlite_client()
    seed_purchase_check_data(session_factory)

    def override_use_cases() -> AiAssistantUseCases:
        session = session_factory()
        return AiAssistantUseCases(
            search_use_cases=FakeSearchUseCases(),
            product_repository=ProductRepository(session),
            evidence_repository=EvidenceRepository(session),
            ai_assistant_provider=FixedPurchaseAssistantProvider(),
        )

    cast(Any, client.app).dependency_overrides[get_ai_assistant_use_cases] = override_use_cases

    response = client.get("/api/v1/ai/products/product-1/purchase-check")

    assert response.status_code == 200
    body = response.json()
    assert body["recommendation"] == "avoid"
    assert body["confidence"] == 0.82
    assert body["summary"] == "AI provider says the current price is too high."
    assert any(item["type"] == "verified_review" for item in body["evidence"])
    assert "proofReference" not in str(body)
    assert "resolutionNote" not in str(body)


def test_purchase_check_returns_product_not_found() -> None:
    client, _session_factory = make_sqlite_client()

    response = client.get("/api/v1/ai/products/missing-product/purchase-check")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def seed_purchase_check_data(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        session.add(
            User(
                id="user-1",
                email="user@example.com",
                nickname="User",
                role="USER",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            Product(
                id="product-1",
                name="Galaxy S26",
                brand="Samsung",
                model_name="SM-S260",
                category="smartphone",
                specs={"storage": "256GB"},
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            Deal(
                id="deal-1",
                product_id="product-1",
                title="Galaxy S26 launch deal",
                source_url="https://example.com/deals/galaxy-s26",
                seller="Example Store",
                original_price=1400000,
                sale_price=990000,
                currency="KRW",
                status="active",
                started_at=None,
                ended_at=None,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add_all(
            [
                PriceHistorySnapshot(
                    id="price-1",
                    product_id="product-1",
                    source_type="deal",
                    source_id="deal-old",
                    price=1200000,
                    currency="KRW",
                    observed_at=NOW,
                    created_at=NOW,
                    updated_at=NOW,
                ),
                PriceHistorySnapshot(
                    id="price-2",
                    product_id="product-1",
                    source_type="deal",
                    source_id="deal-1",
                    price=990000,
                    currency="KRW",
                    observed_at=NOW,
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
        session.add(
            VerifiedReview(
                id="review-1",
                product_id="product-1",
                user_id="user-1",
                rating=5,
                title="실구매 기준 만족",
                body="배송과 제품 상태 모두 좋았습니다.",
                proof_type="receipt",
                proof_reference="order-123",
                status="approved",
                ai_decision="needs_admin_review",
                ai_reason="mock review passed",
                ai_reviewed_at=NOW,
                reviewed_by_user_id=None,
                resolution_note="영수증 확인",
                resolved_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
    finally:
        session.close()
