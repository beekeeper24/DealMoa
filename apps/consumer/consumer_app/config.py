from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConsumerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:5432/dealmoa",
        validation_alias="DATABASE_URL",
    )
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_domain_events_topic: str = Field(
        default="dealmoa.domain-events",
        validation_alias="KAFKA_DOMAIN_EVENTS_TOPIC",
    )
    kafka_search_index_group_id: str = Field(
        default="dealmoa-search-indexer",
        validation_alias="KAFKA_SEARCH_INDEX_GROUP_ID",
    )
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="ELASTICSEARCH_URL",
    )
    consumer_poll_interval_seconds: float = Field(
        default=1.0,
        validation_alias="CONSUMER_POLL_INTERVAL_SECONDS",
    )
    consumer_batch_size: int = Field(default=100, validation_alias="CONSUMER_BATCH_SIZE")
