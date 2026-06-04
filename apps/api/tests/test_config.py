from app.core.config import Settings


def test_settings_reads_oauth2_env_aliases() -> None:
    settings = Settings.model_validate(
        {
            "OAUTH2_GOOGLE_CLIENT_ID": "google-client-id",
            "OAUTH2_GOOGLE_CLIENT_SECRET": "google-client-secret",
            "OAUTH2_KAKAO_CLIENT_ID": "kakao-client-id",
            "OAUTH2_KAKAO_CLIENT_SECRET": "kakao-client-secret",
            "OAUTH2_NAVER_CLIENT_ID": "naver-client-id",
            "OAUTH2_NAVER_CLIENT_SECRET": "naver-client-secret",
        }
    )

    assert settings.oauth_google_client_id == "google-client-id"
    assert settings.oauth_google_client_secret == "google-client-secret"
    assert settings.oauth_kakao_client_id == "kakao-client-id"
    assert settings.oauth_kakao_client_secret == "kakao-client-secret"
    assert settings.oauth_naver_client_id == "naver-client-id"
    assert settings.oauth_naver_client_secret == "naver-client-secret"


def test_settings_reads_ai_review_provider_env() -> None:
    settings = Settings.model_validate(
        {
            "AI_REVIEW_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://api.openai.test/v1",
            "OPENAI_REVIEW_MODEL": "gpt-4o-mini",
            "OPENAI_TIMEOUT_SECONDS": "5.5",
        }
    )

    assert settings.ai_review_provider == "openai"
    assert settings.openai_api_key == "sk-test"
    assert settings.openai_base_url == "https://api.openai.test/v1"
    assert settings.openai_review_model == "gpt-4o-mini"
    assert settings.openai_timeout_seconds == 5.5


def test_settings_reads_ai_review_rate_limit_env() -> None:
    settings = Settings.model_validate(
        {
            "AI_REVIEW_USER_WINDOW_LIMIT": "3",
            "AI_REVIEW_USER_WINDOW_HOURS": "12",
        }
    )

    assert settings.ai_review_user_window_limit == 3
    assert settings.ai_review_user_window_hours == 12
