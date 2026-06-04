from __future__ import annotations

import json
import re
from typing import Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.modules.ai_assistant.schemas import (
    AiSearchTargetType,
    PurchaseRecommendation,
    SearchIntent,
    SearchIntentFilters,
)
from app.modules.evidence.models import PriceHistorySnapshot, VerifiedReview
from app.modules.products.models import Auction, Deal, Product


class PurchaseCheckExplanation(BaseModel):
    recommendation: PurchaseRecommendation
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=500)


class AiAssistantProvider(Protocol):
    def parse_search_intent(self, query: str) -> SearchIntent:
        pass

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        pass


class MockAiAssistantProvider:
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

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        current_prices = [deal.sale_price for deal in deals] + [
            auction.current_price for auction in auctions
        ]
        if not current_prices:
            return PurchaseCheckExplanation(
                recommendation="watch",
                confidence=0.45,
                summary="현재 활성 핫딜이나 경매가 없어 지켜보는 편이 낫습니다.",
            )

        best_current_price = min(current_prices)
        historical_prices = [snapshot.price for snapshot in price_history]
        if not historical_prices:
            return PurchaseCheckExplanation(
                recommendation="watch",
                confidence=0.55,
                summary="현재 구매 후보는 있지만 비교할 가격 이력이 부족합니다.",
            )

        lowest_history_price = min(historical_prices)
        average_history_price = sum(historical_prices) / len(historical_prices)
        if best_current_price <= lowest_history_price and verified_reviews:
            return PurchaseCheckExplanation(
                recommendation="buy",
                confidence=0.78,
                summary=(
                    "현재 가격이 가격 이력 최저가 수준이고 "
                    "승인된 구매 인증 후기가 있어 구매 후보입니다."
                ),
            )
        if best_current_price <= average_history_price:
            return PurchaseCheckExplanation(
                recommendation="buy",
                confidence=0.7,
                summary="현재 가격이 가격 이력 평균보다 낮아 구매 후보입니다.",
            )
        if best_current_price > average_history_price * 1.1:
            return PurchaseCheckExplanation(
                recommendation="avoid",
                confidence=0.65,
                summary="현재 가격이 가격 이력 평균보다 높아 매수 보류가 좋습니다.",
            )
        return PurchaseCheckExplanation(
            recommendation="watch",
            confidence=0.58,
            summary="현재 가격이 가격 이력과 비슷해 추가 가격 변화를 지켜볼 만합니다.",
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


class UnavailableAiAssistantProvider:
    def parse_search_intent(self, query: str) -> SearchIntent:
        raise RuntimeError("AI assistant provider unavailable")

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        raise RuntimeError("AI assistant provider unavailable")


class SafeAiAssistantProvider:
    def __init__(
        self,
        provider: AiAssistantProvider,
        *,
        fallback_provider: AiAssistantProvider | None = None,
    ) -> None:
        self.provider = provider
        self.fallback_provider = fallback_provider or MockAiAssistantProvider()

    def parse_search_intent(self, query: str) -> SearchIntent:
        try:
            return self.provider.parse_search_intent(query)
        except Exception:
            return self.fallback_provider.parse_search_intent(query)

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        try:
            return self.provider.explain_purchase_check(
                product=product,
                deals=deals,
                auctions=auctions,
                price_history=price_history,
                verified_reviews=verified_reviews,
            )
        except Exception:
            return self.fallback_provider.explain_purchase_check(
                product=product,
                deals=deals,
                auctions=auctions,
                price_history=price_history,
                verified_reviews=verified_reviews,
            )


class OpenAiAssistantProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.client = client

    def parse_search_intent(self, query: str) -> SearchIntent:
        response_body = self._post_responses_api(
            {
                "model": self.model,
                "instructions": (
                    "You parse DealMoa Korean commerce searches into safe JSON only. "
                    "Return only allowed target types and filters. Never return raw SQL, "
                    "Elasticsearch DSL, scripts, URLs, or unapproved fields."
                ),
                "input": self._input_payload({"query": query}),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "dealmoa_search_intent",
                        "strict": True,
                        "schema": search_intent_json_schema(),
                    }
                },
                "max_output_tokens": 500,
            }
        )
        return parse_openai_search_intent_response(response_body)

    def explain_purchase_check(
        self,
        *,
        product: Product,
        deals: list[Deal],
        auctions: list[Auction],
        price_history: list[PriceHistorySnapshot],
        verified_reviews: list[VerifiedReview],
    ) -> PurchaseCheckExplanation:
        response_body = self._post_responses_api(
            {
                "model": self.model,
                "instructions": (
                    "You explain whether a DealMoa product is a buy, watch, or avoid. "
                    "Use only the supplied evidence. Do not mention hidden reviews, admin "
                    "notes, proof references, private user ids, or unavailable facts."
                ),
                "input": self._input_payload(
                    {
                        "product": product_payload(product),
                        "current_deals": [deal_payload(deal) for deal in deals[:10]],
                        "current_auctions": [
                            auction_payload(auction) for auction in auctions[:10]
                        ],
                        "price_history": [
                            price_history_payload(snapshot) for snapshot in price_history[:20]
                        ],
                        "verified_reviews": [
                            verified_review_payload(review) for review in verified_reviews[:10]
                        ],
                    }
                ),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "dealmoa_purchase_check",
                        "strict": True,
                        "schema": purchase_check_explanation_json_schema(),
                    }
                },
                "max_output_tokens": 500,
            }
        )
        return parse_openai_purchase_check_response(response_body)

    def _input_payload(self, payload: dict[str, object]) -> list[dict[str, object]]:
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    }
                ],
            }
        ]

    def _post_responses_api(self, payload: dict[str, object]) -> dict[str, object]:
        client = self.client
        if client is not None:
            response = client.post(
                f"{self.base_url}/responses",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return dict(response.json())

        with httpx.Client(timeout=self.timeout_seconds) as created_client:
            response = created_client.post(
                f"{self.base_url}/responses",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return dict(response.json())

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


def product_payload(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "model_name": product.model_name,
        "category": product.category,
        "specs": product.specs,
    }


def deal_payload(deal: Deal) -> dict[str, object]:
    return {
        "id": deal.id,
        "title": deal.title,
        "seller": deal.seller,
        "sale_price": deal.sale_price,
        "original_price": deal.original_price,
        "currency": deal.currency,
    }


def auction_payload(auction: Auction) -> dict[str, object]:
    return {
        "id": auction.id,
        "title": auction.title,
        "seller": auction.seller,
        "current_price": auction.current_price,
        "currency": auction.currency,
        "ends_at": auction.ends_at.isoformat() if auction.ends_at is not None else None,
    }


def price_history_payload(snapshot: PriceHistorySnapshot) -> dict[str, object]:
    return {
        "price": snapshot.price,
        "currency": snapshot.currency,
        "observed_at": snapshot.observed_at.isoformat(),
        "source_type": snapshot.source_type,
    }


def verified_review_payload(review: VerifiedReview) -> dict[str, object]:
    return {
        "id": review.id,
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
    }


def search_intent_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "query": {"type": "string"},
            "normalizedQuery": {"type": "string"},
            "targetTypes": {
                "type": "array",
                "items": {"type": "string", "enum": ["products", "deals", "auctions"]},
                "minItems": 1,
            },
            "filters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category": {"type": ["string", "null"]},
                    "maxPrice": {"type": ["integer", "null"], "minimum": 0},
                },
                "required": ["category", "maxPrice"],
            },
        },
        "required": ["query", "normalizedQuery", "targetTypes", "filters"],
    }


def purchase_check_explanation_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "recommendation": {
                "type": "string",
                "enum": ["buy", "watch", "avoid"],
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "summary": {
                "type": "string",
            },
        },
        "required": ["recommendation", "confidence", "summary"],
    }


def parse_openai_search_intent_response(response_body: dict[str, object]) -> SearchIntent:
    text = extract_output_text(response_body)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI search intent response was not JSON") from exc
    try:
        return SearchIntent.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("OpenAI search intent response failed validation") from exc


def parse_openai_purchase_check_response(
    response_body: dict[str, object],
) -> PurchaseCheckExplanation:
    text = extract_output_text(response_body)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI purchase check response was not JSON") from exc
    try:
        return PurchaseCheckExplanation.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("OpenAI purchase check response failed validation") from exc


def extract_output_text(response_body: dict[str, object]) -> str:
    output_text = response_body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = response_body.get("output")
    if isinstance(output, list):
        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str):
                    texts.append(text)
        joined = "".join(texts).strip()
        if joined:
            return joined

    raise ValueError("OpenAI assistant response did not include output text")
