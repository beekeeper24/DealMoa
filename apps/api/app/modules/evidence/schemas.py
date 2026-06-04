from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

ReviewStatus = Literal["pending_review", "approved", "rejected", "hidden"]
ReviewAction = Literal["approve", "reject", "hide", "restore"]


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class PriceHistorySnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    source_type: str = Field(alias="sourceType")
    source_id: str = Field(alias="sourceId")
    price: int
    currency: str
    observed_at: datetime = Field(alias="observedAt")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("observed_at", "created_at")
    def serialize_timestamps(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class PriceHistoryListResponse(BaseModel):
    items: list[PriceHistorySnapshotResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class VerifiedReviewCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=4000)
    proof_type: str = Field(alias="proofType", min_length=1, max_length=80)
    proof_reference: str = Field(alias="proofReference", min_length=1, max_length=255)


class VerifiedReviewReviewRequest(BaseModel):
    action: ReviewAction
    resolution_note: str | None = Field(default=None, alias="resolutionNote", max_length=2000)


class VerifiedReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    user_id: str = Field(alias="userId")
    rating: int
    title: str
    body: str
    proof_type: str = Field(alias="proofType")
    proof_reference: str | None = Field(alias="proofReference")
    status: str
    ai_decision: str | None = Field(alias="aiDecision")
    ai_reason: str | None = Field(alias="aiReason")
    ai_reviewed_at: datetime | None = Field(alias="aiReviewedAt")
    reviewed_by_user_id: str | None = Field(alias="reviewedByUserId")
    resolution_note: str | None = Field(alias="resolutionNote")
    resolved_at: datetime | None = Field(alias="resolvedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("ai_reviewed_at", "resolved_at", "created_at", "updated_at")
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class VerifiedReviewListResponse(BaseModel):
    items: list[VerifiedReviewResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class PublicVerifiedReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    rating: int
    title: str
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("created_at", "updated_at")
    def serialize_timestamps(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class PublicVerifiedReviewListResponse(BaseModel):
    items: list[PublicVerifiedReviewResponse]
    next_cursor: str | None = Field(alias="nextCursor")
