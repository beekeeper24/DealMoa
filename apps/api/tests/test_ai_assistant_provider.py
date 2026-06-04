import json
from typing import Any

import httpx
from app.core.config import Settings
from app.modules.ai_assistant.factory import create_ai_assistant_provider
from app.modules.ai_assistant.provider import (
    MockAiAssistantProvider,
    OpenAiAssistantProvider,
    PurchaseCheckExplanation,
    SafeAiAssistantProvider,
)
from app.modules.evidence.models import VerifiedReview
from app.modules.products.models import Product


def test_mock_ai_assistant_provider_preserves_current_search_intent() -> None:
    provider = MockAiAssistantProvider()

    intent = provider.parse_search_intent("갤럭시 100만원 이하 핫딜 찾아줘")

    assert intent.normalized_query == "갤럭시 100만원 이하 핫딜 찾아줘"
    assert intent.target_types == ["deals"]
    assert intent.filters.max_price == 1000000


def test_openai_assistant_provider_uses_structured_schema_for_search_intent() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "output_text": json.dumps(
                    {
                        "query": "출퇴근용 무선 이어폰",
                        "normalizedQuery": "출퇴근용 무선 이어폰",
                        "targetTypes": ["products"],
                        "filters": {
                            "category": "earphones",
                            "maxPrice": 250000,
                        },
                    },
                    ensure_ascii=False,
                )
            },
        )

    provider = OpenAiAssistantProvider(
        api_key="sk-test",
        base_url="https://api.openai.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        model="gpt-4o-mini",
        timeout_seconds=3.0,
    )

    intent = provider.parse_search_intent("출퇴근용 무선 이어폰")

    assert intent.target_types == ["products"]
    assert intent.filters.category == "earphones"
    assert intent.filters.max_price == 250000
    assert captured["url"] == "https://api.openai.test/v1/responses"
    assert captured["headers"]["authorization"] == "Bearer sk-test"
    assert captured["body"]["model"] == "gpt-4o-mini"
    assert captured["body"]["text"]["format"]["type"] == "json_schema"
    assert captured["body"]["text"]["format"]["strict"] is True
    assert captured["body"]["text"]["format"]["schema"]["additionalProperties"] is False


def test_safe_assistant_provider_falls_back_to_mock_search_intent_on_invalid_output() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output_text": json.dumps({"targetTypes": ["unsafe"]})})

    provider = SafeAiAssistantProvider(
        OpenAiAssistantProvider(
            api_key="sk-test",
            base_url="https://api.openai.test/v1",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            model="gpt-4o-mini",
            timeout_seconds=3.0,
        )
    )

    intent = provider.parse_search_intent("노트북 핫딜")

    assert intent.target_types == ["deals"]
    assert intent.filters.category == "laptop"


def test_openai_purchase_check_does_not_send_internal_review_metadata() -> None:
    captured_body = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = request.content.decode()
        return httpx.Response(
            200,
            json={
                "output_text": json.dumps(
                    {
                        "recommendation": "watch",
                        "confidence": 0.63,
                        "summary": "가격 이력이 더 필요합니다.",
                    },
                    ensure_ascii=False,
                )
            },
        )

    provider = OpenAiAssistantProvider(
        api_key="sk-test",
        base_url="https://api.openai.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        model="gpt-4o-mini",
        timeout_seconds=3.0,
    )

    explanation = provider.explain_purchase_check(
        product=Product(
            id="product-1",
            name="Galaxy S26",
            brand="Samsung",
            model_name="SM-S260",
            category="smartphone",
            specs={"storage": "256GB"},
        ),
        deals=[],
        auctions=[],
        price_history=[],
        verified_reviews=[
            VerifiedReview(
                id="review-1",
                product_id="product-1",
                user_id="user-1",
                rating=5,
                title="실구매 만족",
                body="배송이 빨랐습니다.",
                proof_type="receipt",
                proof_reference="order-secret-123",
                status="approved",
                ai_reason="internal review reason",
                resolution_note="internal admin note",
            )
        ],
    )

    assert explanation == PurchaseCheckExplanation(
        recommendation="watch",
        confidence=0.63,
        summary="가격 이력이 더 필요합니다.",
    )
    assert "실구매 만족" in captured_body
    assert "order-secret-123" not in captured_body
    assert "internal review reason" not in captured_body
    assert "internal admin note" not in captured_body


def test_openai_assistant_provider_without_api_key_falls_back_to_mock() -> None:
    provider = create_ai_assistant_provider(
        Settings.model_validate(
            {
                "AI_ASSISTANT_PROVIDER": "openai",
                "OPENAI_API_KEY": "",
            }
        )
    )

    intent = provider.parse_search_intent("경매 찾아줘")

    assert intent.target_types == ["auctions"]
