from __future__ import annotations

from typing import Any, Protocol

from app.core.exceptions import ProductNotFoundException
from app.core.pagination import CursorPage
from app.modules.ai_assistant.provider import AiAssistantProvider, MockAiAssistantProvider
from app.modules.ai_assistant.schemas import (
    AiSearchRequest,
    AiSearchResponse,
    AiSearchTargetType,
    ProductPurchaseCheckResponse,
    PurchaseCheckEvidence,
    SearchIntent,
)
from app.modules.evidence.models import PriceHistorySnapshot, VerifiedReview
from app.modules.evidence.repository import EvidenceRepository
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.search.schemas import (
    AuctionSearchItem,
    AuctionSearchResponse,
    DealSearchItem,
    DealSearchResponse,
    ProductSearchItem,
    ProductSearchResponse,
)


class SearchUseCasesProtocol(Protocol):
    def search_products(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass

    def search_deals(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass

    def search_auctions(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass


class AiAssistantUseCases:
    def __init__(
        self,
        *,
        search_use_cases: SearchUseCasesProtocol,
        product_repository: ProductRepository,
        evidence_repository: EvidenceRepository,
        ai_assistant_provider: AiAssistantProvider | None = None,
    ) -> None:
        self.search_use_cases = search_use_cases
        self.product_repository = product_repository
        self.evidence_repository = evidence_repository
        self.ai_assistant_provider = ai_assistant_provider or MockAiAssistantProvider()

    def search(self, request: AiSearchRequest) -> AiSearchResponse:
        intent = self.ai_assistant_provider.parse_search_intent(request.query)
        products = ProductSearchResponse(items=[], nextCursor=None)
        deals = DealSearchResponse(items=[], nextCursor=None)
        auctions = AuctionSearchResponse(items=[], nextCursor=None)

        if "products" in intent.target_types:
            page = self.search_use_cases.search_products(
                query=request.query,
                limit=request.limit,
                cursor=None,
            )
            products = ProductSearchResponse(
                items=[ProductSearchItem.model_validate(item) for item in page.items],
                nextCursor=page.next_cursor,
            )
        if "deals" in intent.target_types:
            page = self.search_use_cases.search_deals(
                query=request.query,
                limit=request.limit,
                cursor=None,
            )
            deals = DealSearchResponse(
                items=[DealSearchItem.model_validate(item) for item in page.items],
                nextCursor=page.next_cursor,
            )
        if "auctions" in intent.target_types:
            page = self.search_use_cases.search_auctions(
                query=request.query,
                limit=request.limit,
                cursor=None,
            )
            auctions = AuctionSearchResponse(
                items=[AuctionSearchItem.model_validate(item) for item in page.items],
                nextCursor=page.next_cursor,
            )

        return AiSearchResponse(
            intent=intent,
            summary=self._search_summary(intent.target_types, products, deals, auctions),
            products=products,
            deals=deals,
            auctions=auctions,
        )

    def parse_search_intent(self, query: str) -> SearchIntent:
        return self.ai_assistant_provider.parse_search_intent(query)

    def purchase_check(self, product_id: str) -> ProductPurchaseCheckResponse:
        product = self.product_repository.get_product(product_id)
        if product is None:
            raise ProductNotFoundException(product_id)

        deals = [
            deal
            for deal in self.product_repository.list_deals_for_product(
                product_id,
                limit=20,
                cursor=None,
            ).items
            if deal.status == "active"
        ]
        auctions = [
            auction
            for auction in self.product_repository.list_auctions_for_product(
                product_id,
                limit=20,
                cursor=None,
            ).items
            if auction.status == "active"
        ]
        price_history = self.evidence_repository.list_price_history(
            product_id=product_id,
            limit=20,
            cursor=None,
        ).items
        verified_reviews = self.evidence_repository.list_product_verified_reviews(
            product_id=product_id,
            limit=10,
            cursor=None,
        ).items

        explanation = self.ai_assistant_provider.explain_purchase_check(
            product=product,
            deals=deals,
            auctions=auctions,
            price_history=price_history,
            verified_reviews=verified_reviews,
        )
        return ProductPurchaseCheckResponse(
            productId=product.id,
            recommendation=explanation.recommendation,
            confidence=explanation.confidence,
            summary=explanation.summary,
            evidence=self._build_evidence(
                product=product,
                deals=deals,
                auctions=auctions,
                price_history=price_history,
                verified_reviews=verified_reviews,
            ),
        )

    def _search_summary(
        self,
        target_types: list[AiSearchTargetType],
        products: ProductSearchResponse,
        deals: DealSearchResponse,
        auctions: AuctionSearchResponse,
    ) -> str:
        total = len(products.items) + len(deals.items) + len(auctions.items)
        label = self._target_label(target_types)
        return f"{label} 중심으로 {total}개 후보를 찾았습니다."

    def _target_label(self, target_types: list[AiSearchTargetType]) -> str:
        if target_types == ["products"]:
            return "상품"
        if target_types == ["deals"]:
            return "핫딜"
        if target_types == ["auctions"]:
            return "경매"
        return "상품/핫딜/경매"

    def _build_evidence(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> list[PurchaseCheckEvidence]:
        evidence: list[PurchaseCheckEvidence] = []
        best_deal = min(deals, key=lambda deal: deal.sale_price, default=None)
        best_auction = min(auctions, key=lambda auction: auction.current_price, default=None)
        if best_deal is not None:
            evidence.append(
                PurchaseCheckEvidence(
                    type="current_deal",
                    label="최저 핫딜",
                    value=f"{best_deal.title} / {best_deal.sale_price:,} {best_deal.currency}",
                    sourceType="deal",
                    sourceId=best_deal.id,
                )
            )
        if best_auction is not None:
            evidence.append(
                PurchaseCheckEvidence(
                    type="current_auction",
                    label="최저 경매",
                    value=(
                        f"{best_auction.title} / "
                        f"{best_auction.current_price:,} {best_auction.currency}"
                    ),
                    sourceType="auction",
                    sourceId=best_auction.id,
                )
            )
        if price_history:
            prices = [snapshot.price for snapshot in price_history]
            evidence.append(
                PurchaseCheckEvidence(
                    type="price_history",
                    label="가격 이력",
                    value=f"최저 {min(prices):,} / 평균 {int(sum(prices) / len(prices)):,} KRW",
                    sourceType="price_history",
                )
            )
        for review in verified_reviews[:2]:
            evidence.append(
                PurchaseCheckEvidence(
                    type="verified_review",
                    label=f"인증 후기 평점 {review.rating}/5",
                    value=f"{review.title}: {review.body}",
                    sourceType="verified_review",
                    sourceId=review.id,
                )
            )
        if product.specs:
            evidence.append(
                PurchaseCheckEvidence(
                    type="product_specs",
                    label="상품 스펙",
                    value=", ".join(f"{key}: {value}" for key, value in product.specs.items()),
                    sourceType="product",
                    sourceId=product.id,
                )
            )
        return evidence[:8]
