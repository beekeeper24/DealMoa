from functools import lru_cache

from pydantic import Field
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
