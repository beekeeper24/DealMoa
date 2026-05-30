from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.modules.admin.schemas import OfferStatus

ReportTargetType = Literal["deal", "auction"]
ReportStatus = Literal["open", "resolved", "dismissed"]
ReportReviewStatus = Literal["resolved", "dismissed"]


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class ReportCreateRequest(BaseModel):
    reason_code: str = Field(alias="reasonCode", min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=2000)


class ReportReviewRequest(BaseModel):
    status: ReportReviewStatus
    resolution_note: str | None = Field(default=None, alias="resolutionNote", max_length=2000)
    target_status: OfferStatus | None = Field(default=None, alias="targetStatus")


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    target_type: str = Field(alias="targetType")
    target_id: str = Field(alias="targetId")
    reason_code: str = Field(alias="reasonCode")
    description: str | None = None
    status: str
    reviewed_by_user_id: str | None = Field(default=None, alias="reviewedByUserId")
    resolution_note: str | None = Field(default=None, alias="resolutionNote")
    resolved_at: datetime | None = Field(default=None, alias="resolvedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("resolved_at")
    def serialize_resolved_at(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    next_cursor: str | None = Field(alias="nextCursor")
