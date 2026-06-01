from __future__ import annotations

import json
from typing import Literal, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.modules.evidence.schemas import VerifiedReviewCreateRequest
from app.modules.submissions.schemas import SubmissionCreateRequest

AIReviewDecision = Literal["needs_admin_review", "reject_candidate"]


class AIReviewResult(BaseModel):
    decision: AIReviewDecision
    reason: str = Field(min_length=1, max_length=500)


class AiReviewProvider(Protocol):
    def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
        pass

    def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        pass


class MockAiReviewProvider:
    def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
        return AIReviewResult(
            decision="needs_admin_review",
            reason="mock review passed: admin approval required",
        )

    def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        return AIReviewResult(
            decision="needs_admin_review",
            reason="mock review passed: receipt proof requires admin approval",
        )


class UnavailableAiReviewProvider:
    def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
        raise RuntimeError("AI review provider unavailable")

    def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        raise RuntimeError("AI review provider unavailable")


class SafeAiReviewProvider:
    def __init__(
        self,
        provider: AiReviewProvider,
        *,
        fallback_reason: str = "ai review unavailable: admin approval required",
    ) -> None:
        self.provider = provider
        self.fallback_reason = fallback_reason

    def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
        try:
            return self.provider.review_submission(request)
        except Exception:
            return self._fallback()

    def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        try:
            return self.provider.review_verified_review(request)
        except Exception:
            return self._fallback()

    def _fallback(self) -> AIReviewResult:
        return AIReviewResult(
            decision="needs_admin_review",
            reason=self.fallback_reason,
        )


class OpenAiReviewProvider:
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

    def review_submission(self, request: SubmissionCreateRequest) -> AIReviewResult:
        return self._review(
            target_type="submission",
            payload={
                "offer_type": request.offer_type,
                "source_host": urlparse(request.source_url).netloc,
                "product_name": request.product_name,
                "brand": request.brand,
                "model_name": request.model_name,
                "category": request.category,
                "title": request.title,
                "seller": request.seller,
                "original_price": request.original_price,
                "sale_price": request.sale_price,
                "current_price": request.current_price,
                "currency": request.currency,
                "description": request.description,
            },
        )

    def review_verified_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        return self._review(
            target_type="verified_review",
            payload={
                "rating": request.rating,
                "title": request.title,
                "body": request.body,
                "proof_type": request.proof_type,
                "proof_reference_present": request.proof_reference is not None,
            },
        )

    def _review(self, *, target_type: str, payload: dict[str, object]) -> AIReviewResult:
        response_body = self._post_responses_api(
            {
                "model": self.model,
                "instructions": (
                    "You are DealMoa's first-pass review classifier. "
                    "Return JSON only. Never approve publication. "
                    "Use needs_admin_review for ordinary cases and reject_candidate only for "
                    "clearly unsafe, spammy, impossible, or policy-violating input."
                ),
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": json.dumps(
                                    {
                                        "target_type": target_type,
                                        "candidate": payload,
                                    },
                                    ensure_ascii=False,
                                    sort_keys=True,
                                ),
                            }
                        ],
                    }
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "dealmoa_ai_review",
                        "strict": True,
                        "schema": review_result_json_schema(),
                    }
                },
                "max_output_tokens": 300,
            }
        )
        return parse_openai_review_response(response_body)

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


def review_result_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["needs_admin_review", "reject_candidate"],
            },
            "reason": {
                "type": "string",
            },
        },
        "required": ["decision", "reason"],
    }


def parse_openai_review_response(response_body: dict[str, object]) -> AIReviewResult:
    text = extract_output_text(response_body)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI review response was not JSON") from exc
    try:
        return AIReviewResult.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("OpenAI review response failed validation") from exc


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

    raise ValueError("OpenAI review response did not include output text")
