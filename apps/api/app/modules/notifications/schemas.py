from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    type: str
    title: str
    body: str
    target_type: str | None = Field(alias="targetType")
    target_id: str | None = Field(alias="targetId")
    metadata_json: dict[str, object] = Field(alias="metadata")
    read_at: datetime | None = Field(alias="readAt")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("read_at", "created_at")
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class UnreadNotificationCountResponse(BaseModel):
    count: int


class MarkAllNotificationsReadResponse(BaseModel):
    updated_count: int = Field(alias="updatedCount")
