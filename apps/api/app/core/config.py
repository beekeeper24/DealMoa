from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="local", validation_alias="API_ENV")
    project_name: str = Field(default="DealMoa API", validation_alias="API_PROJECT_NAME")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    database_url: str = Field(
        default="postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:5432/dealmoa",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="ELASTICSEARCH_URL",
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
