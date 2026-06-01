from app.core.config import Settings
from app.modules.ai_review.provider import (
    AiReviewProvider,
    MockAiReviewProvider,
    OpenAiReviewProvider,
    SafeAiReviewProvider,
    UnavailableAiReviewProvider,
)


def create_ai_review_provider(settings: Settings) -> AiReviewProvider:
    if settings.ai_review_provider == "openai" and settings.openai_api_key:
        return SafeAiReviewProvider(
            OpenAiReviewProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_review_model,
                timeout_seconds=settings.openai_timeout_seconds,
            )
        )
    if settings.ai_review_provider == "openai":
        return SafeAiReviewProvider(
            UnavailableAiReviewProvider(),
            fallback_reason="ai review unavailable: OpenAI API key not configured",
        )
    return MockAiReviewProvider()
