from __future__ import annotations

import re
from typing import Any, Protocol

from app.core.exceptions import ProductNotFoundException
from app.core.pagination import CursorPage
from app.modules.ai_assistant.schemas import (
    AiSearchRequest,
    AiSearchResponse,
    AiSearchTargetType,
    ProductPurchaseCheckResponse,
    PurchaseCheckEvidence,
    PurchaseRecommendation,
    SearchIntent,
    SearchIntentFilters,
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
    ) -> None:
        self.search_use_cases = search_use_cases
        self.product_repository = product_repository
        self.evidence_repository = evidence_repository

    def search(self, request: AiSearchRequest) -> AiSearchResponse:
        intent = self.parse_search_intent(request.query)
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
        normalized_query = " ".join(query.strip().lower().split())
        return SearchIntent(
            query=query,
            normalizedQuery=normalized_query,
            targetTypes=self._extract_target_types(normalized_query),
            filters=SearchIntentFilters(
                category=self._extract_category(normalized_query),
                maxPrice=self._extract_max_price(normalized_query),
            ),
        )

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

        recommendation, confidence, summary = self._recommend(
            deals=deals,
            auctions=auctions,
            price_history=price_history,
            verified_reviews=verified_reviews,
        )
        return ProductPurchaseCheckResponse(
            productId=product.id,
            recommendation=recommendation,
            confidence=confidence,
            summary=summary,
            evidence=self._build_evidence(
                product=product,
                deals=deals,
                auctions=auctions,
                price_history=price_history,
                verified_reviews=verified_reviews,
            ),
        )

    def _extract_target_types(self, normalized_query: str) -> list[AiSearchTargetType]:
        targets: list[AiSearchTargetType] = []
        if any(keyword in normalized_query for keyword in ("상품", "제품", "스펙")):
            targets.append("products")
        if any(keyword in normalized_query for keyword in ("핫딜", "딜", "할인", "특가")):
            targets.append("deals")
        if any(keyword in normalized_query for keyword in ("경매", "입찰")):
            targets.append("auctions")
        return targets or ["products", "deals", "auctions"]

    def _extract_category(self, normalized_query: str) -> str | None:
        if any(keyword in normalized_query for keyword in ("스마트폰", "휴대폰", "핸드폰", "폰")):
            return "smartphone"
        if any(keyword in normalized_query for keyword in ("노트북", "랩탑")):
            return "laptop"
        return None

    def _extract_max_price(self, normalized_query: str) -> int | None:
        manwon_match = re.search(r"(\d[\d,]*)\s*만\s*원", normalized_query)
        if manwon_match:
            return int(manwon_match.group(1).replace(",", "")) * 10000

        won_match = re.search(r"(\d[\d,]*)\s*원", normalized_query)
        if won_match:
            return int(won_match.group(1).replace(",", ""))
        return None

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

    def _recommend(
        self,
        *,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> tuple[PurchaseRecommendation, float, str]:
        current_prices = [deal.sale_price for deal in deals] + [
            auction.current_price for auction in auctions
        ]
        if not current_prices:
            return "watch", 0.45, "현재 활성 핫딜이나 경매가 없어 지켜보는 편이 낫습니다."

        best_current_price = min(current_prices)
        historical_prices = [snapshot.price for snapshot in price_history]
        if not historical_prices:
            return "watch", 0.55, "현재 구매 후보는 있지만 비교할 가격 이력이 부족합니다."

        lowest_history_price = min(historical_prices)
        average_history_price = sum(historical_prices) / len(historical_prices)
        if best_current_price <= lowest_history_price and verified_reviews:
            return (
                "buy",
                0.78,
                "현재 가격이 가격 이력 최저가 수준이고 "
                "승인된 구매 인증 후기가 있어 구매 후보입니다.",
            )
        if best_current_price <= average_history_price:
            return "buy", 0.7, "현재 가격이 가격 이력 평균보다 낮아 구매 후보입니다."
        if best_current_price > average_history_price * 1.1:
            return "avoid", 0.65, "현재 가격이 가격 이력 평균보다 높아 매수 보류가 좋습니다."
        return "watch", 0.58, "현재 가격이 가격 이력과 비슷해 추가 가격 변화를 지켜볼 만합니다."

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
