from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def serialize_utc_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class CrawlerRunLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    task_name: str = Field(alias="taskName")
    status: str
    scanned_count: int = Field(alias="scanned")
    fetched_count: int = Field(alias="fetched")
    accepted_count: int = Field(alias="accepted")
    created_count: int = Field(alias="created")
    duplicate_count: int = Field(alias="duplicates")
    skipped_count: int = Field(alias="skipped")
    skip_reasons_json: dict[str, int] = Field(alias="skipReasons")
    error_type: str | None = Field(default=None, alias="errorType")
    error_message: str | None = Field(default=None, alias="errorMessage")
    started_at: datetime = Field(alias="startedAt")
    finished_at: datetime = Field(alias="finishedAt")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("started_at")
    def serialize_started_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value)

    @field_serializer("finished_at")
    def serialize_finished_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value)


class CrawlerRunLogListResponse(BaseModel):
    items: list[CrawlerRunLogResponse]
    next_cursor: str | None = Field(alias="nextCursor")
