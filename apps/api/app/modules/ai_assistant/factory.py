from app.core.config import Settings
from app.modules.ai_assistant.provider import (
    AiAssistantProvider,
    MockAiAssistantProvider,
    OpenAiAssistantProvider,
    SafeAiAssistantProvider,
    UnavailableAiAssistantProvider,
)


def create_ai_assistant_provider(settings: Settings) -> AiAssistantProvider:
    if settings.ai_assistant_provider == "openai" and settings.openai_api_key:
        return SafeAiAssistantProvider(
            OpenAiAssistantProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_assistant_model,
                timeout_seconds=settings.openai_timeout_seconds,
            )
        )
    if settings.ai_assistant_provider == "openai":
        return SafeAiAssistantProvider(UnavailableAiAssistantProvider())
    return MockAiAssistantProvider()
