import json
from typing import Any

import httpx
from app.core.config import Settings
from app.modules.ai_review.factory import create_ai_review_provider
from app.modules.ai_review.provider import (
    AIReviewResult,
    MockAiReviewProvider,
    OpenAiReviewProvider,
    SafeAiReviewProvider,
)
from app.modules.evidence.schemas import VerifiedReviewCreateRequest
from app.modules.submissions.schemas import SubmissionCreateRequest


def submission_request() -> SubmissionCreateRequest:
    return SubmissionCreateRequest(
        offerType="deal",
        sourceUrl="https://example.com/deals/galaxy-s26",
        productName="Galaxy S26",
        brand="Samsung",
        modelName="SM-S260",
        category="smartphone",
        title="Galaxy S26 launch deal",
        seller="Example Store",
        originalPrice=1400000,
        salePrice=1090000,
        currentPrice=None,
        currency="KRW",
        description="Launch discount",
    )


def verified_review_request() -> VerifiedReviewCreateRequest:
    return VerifiedReviewCreateRequest(
        rating=5,
        title="실구매 기준 만족",
        body="배송과 제품 상태 모두 좋았습니다.",
        proofType="receipt",
        proofReference="order-123-secret",
    )


def test_mock_ai_review_provider_preserves_current_submission_output() -> None:
    provider = MockAiReviewProvider()

    result = provider.review_submission(submission_request())

    assert result == AIReviewResult(
        decision="needs_admin_review",
        reason="mock review passed: admin approval required",
    )


def test_openai_review_provider_uses_structured_responses_schema() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "decision": "reject_candidate",
                                        "reason": "source looks suspicious",
                                    }
                                ),
                            }
                        ]
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAiReviewProvider(
        api_key="sk-test",
        base_url="https://api.openai.test/v1",
        client=client,
        model="gpt-4o-mini",
        timeout_seconds=3.0,
    )

    result = provider.review_submission(submission_request())

    assert result == AIReviewResult(
        decision="reject_candidate",
        reason="source looks suspicious",
    )
    assert captured["url"] == "https://api.openai.test/v1/responses"
    assert captured["headers"]["authorization"] == "Bearer sk-test"
    assert captured["body"]["model"] == "gpt-4o-mini"
    assert captured["body"]["text"]["format"]["type"] == "json_schema"
    assert captured["body"]["text"]["format"]["strict"] is True
    assert captured["body"]["text"]["format"]["schema"]["additionalProperties"] is False
    assert "Galaxy S26 launch deal" in json.dumps(captured["body"], ensure_ascii=False)


def test_openai_review_provider_does_not_send_verified_review_proof_reference() -> None:
    captured_body = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = request.content.decode()
        return httpx.Response(
            200,
            json={
                "output_text": json.dumps(
                    {
                        "decision": "needs_admin_review",
                        "reason": "receipt proof requires admin review",
                    }
                )
            },
        )

    provider = OpenAiReviewProvider(
        api_key="sk-test",
        base_url="https://api.openai.test/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        model="gpt-4o-mini",
        timeout_seconds=3.0,
    )

    result = provider.review_verified_review(verified_review_request())

    assert result.decision == "needs_admin_review"
    assert "order-123-secret" not in captured_body
    assert "proof_reference_present" in captured_body


def test_safe_ai_review_provider_falls_back_to_admin_review() -> None:
    class FailingProvider:
        def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
            raise RuntimeError("provider unavailable")

        def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
            raise RuntimeError("provider unavailable")

    provider = SafeAiReviewProvider(FailingProvider())

    result = provider.review_submission(submission_request())

    assert result == AIReviewResult(
        decision="needs_admin_review",
        reason="ai review unavailable: admin approval required",
    )


def test_openai_provider_without_api_key_falls_back_to_admin_review() -> None:
    provider = create_ai_review_provider(
        Settings.model_validate(
            {
                "AI_REVIEW_PROVIDER": "openai",
                "OPENAI_API_KEY": "",
            }
        )
    )

    result = provider.review_submission(submission_request())

    assert result == AIReviewResult(
        decision="needs_admin_review",
        reason="ai review unavailable: OpenAI API key not configured",
    )
