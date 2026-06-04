from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

DiscussionStatus = Literal["visible", "hidden"]
DiscussionModerationAction = Literal["hide", "restore"]
DiscussionRiskLevel = Literal["low", "medium", "high"]


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class DiscussionCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class DiscussionModerationRequest(BaseModel):
    action: DiscussionModerationAction
    moderation_note: str | None = Field(default=None, alias="moderationNote", max_length=2000)


class PublicDiscussionCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    user_nickname: str = Field(alias="userNickname")
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("created_at", "updated_at")
    def serialize_timestamps(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class DiscussionCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    user_id: str = Field(alias="userId")
    user_nickname: str = Field(alias="userNickname")
    body: str
    status: DiscussionStatus
    moderation_risk_score: int = Field(alias="riskScore")
    moderation_risk_level: DiscussionRiskLevel = Field(alias="riskLevel")
    moderation_risk_reasons_json: list[str] = Field(alias="riskReasons")
    moderated_by_user_id: str | None = Field(alias="moderatedByUserId")
    moderation_note: str | None = Field(alias="moderationNote")
    moderated_at: datetime | None = Field(alias="moderatedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("moderated_at", "created_at", "updated_at")
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class PublicDiscussionListResponse(BaseModel):
    items: list[PublicDiscussionCommentResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class DiscussionListResponse(BaseModel):
    items: list[DiscussionCommentResponse]
    next_cursor: str | None = Field(alias="nextCursor")
