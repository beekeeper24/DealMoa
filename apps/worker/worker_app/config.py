from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:5432/dealmoa",
        validation_alias="DATABASE_URL",
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        validation_alias="CELERY_RESULT_BACKEND",
    )
    auction_ending_soon_lookahead_minutes: int = Field(
        default=60,
        validation_alias="AUCTION_ENDING_SOON_LOOKAHEAD_MINUTES",
    )
    auction_ending_soon_batch_size: int = Field(
        default=100,
        validation_alias="AUCTION_ENDING_SOON_BATCH_SIZE",
    )
    auction_ending_soon_schedule_seconds: int = Field(
        default=300,
        validation_alias="AUCTION_ENDING_SOON_SCHEDULE_SECONDS",
    )
    crawler_system_user_id: str = Field(
        default="system-crawler",
        validation_alias="CRAWLER_SYSTEM_USER_ID",
    )
    crawler_system_user_email: str = Field(
        default="crawler@dealmoa.local",
        validation_alias="CRAWLER_SYSTEM_USER_EMAIL",
    )
    crawler_system_user_nickname: str = Field(
        default="DealMoa Crawler",
        validation_alias="CRAWLER_SYSTEM_USER_NICKNAME",
    )
