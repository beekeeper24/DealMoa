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
