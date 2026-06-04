from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="local", validation_alias="API_ENV")
    project_name: str = Field(default="DealMoa API", validation_alias="API_PROJECT_NAME")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    api_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3100",
        validation_alias="API_CORS_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:5432/dealmoa",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_BROKER_URL",
    )
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="ELASTICSEARCH_URL",
    )
    ai_review_provider: Literal["mock", "openai"] = Field(
        default="mock",
        validation_alias="AI_REVIEW_PROVIDER",
    )
    ai_assistant_provider: Literal["mock", "openai"] = Field(
        default="mock",
        validation_alias="AI_ASSISTANT_PROVIDER",
    )
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    openai_review_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_REVIEW_MODEL",
    )
    openai_assistant_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_ASSISTANT_MODEL",
    )
    openai_timeout_seconds: float = Field(
        default=8.0,
        validation_alias="OPENAI_TIMEOUT_SECONDS",
    )
    ai_review_user_window_limit: int = Field(
        default=20,
        ge=0,
        validation_alias="AI_REVIEW_USER_WINDOW_LIMIT",
    )
    ai_review_user_window_hours: int = Field(
        default=24,
        ge=1,
        validation_alias="AI_REVIEW_USER_WINDOW_HOURS",
    )
    jwt_secret_key: str = Field(
        default="replace-with-local-jwt-secret-minimum-32-bytes",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=14,
        validation_alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    )
    auth_refresh_cookie_name: str = Field(
        default="dm_refresh_token",
        validation_alias="AUTH_REFRESH_COOKIE_NAME",
    )
    auth_refresh_cookie_secure: bool = Field(
        default=False,
        validation_alias="AUTH_REFRESH_COOKIE_SECURE",
    )
    auth_refresh_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        validation_alias="AUTH_REFRESH_COOKIE_SAMESITE",
    )
    oauth_google_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("OAUTH_GOOGLE_CLIENT_ID", "OAUTH2_GOOGLE_CLIENT_ID"),
    )
    oauth_google_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OAUTH_GOOGLE_CLIENT_SECRET",
            "OAUTH2_GOOGLE_CLIENT_SECRET",
        ),
    )
    oauth_kakao_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("OAUTH_KAKAO_CLIENT_ID", "OAUTH2_KAKAO_CLIENT_ID"),
    )
    oauth_kakao_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OAUTH_KAKAO_CLIENT_SECRET",
            "OAUTH2_KAKAO_CLIENT_SECRET",
        ),
    )
    oauth_naver_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("OAUTH_NAVER_CLIENT_ID", "OAUTH2_NAVER_CLIENT_ID"),
    )
    oauth_naver_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OAUTH_NAVER_CLIENT_SECRET",
            "OAUTH2_NAVER_CLIENT_SECRET",
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
