from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

OfferType = Literal["deal", "auction"]
SubmissionStatus = Literal["pending_review", "approved", "rejected"]
SubmissionReviewAction = Literal["approve", "reject"]


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class SubmissionCreateRequest(BaseModel):
    offer_type: OfferType = Field(alias="offerType")
    source_url: str = Field(alias="sourceUrl", min_length=1, max_length=2000)
    product_name: str = Field(alias="productName", min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=120)
    model_name: str | None = Field(default=None, alias="modelName", max_length=120)
    category: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    seller: str | None = Field(default=None, max_length=120)
    original_price: int | None = Field(default=None, alias="originalPrice", ge=0)
    sale_price: int | None = Field(default=None, alias="salePrice", ge=0)
    current_price: int | None = Field(default=None, alias="currentPrice", ge=0)
    currency: str = Field(default="KRW", min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        trimmed = value.strip()
        parsed = urlparse(trimmed)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise PydanticCustomError(
                "source_url_scheme",
                "sourceUrl must be an http or https URL",
            )
        return trimmed

    @model_validator(mode="after")
    def validate_offer_price(self) -> "SubmissionCreateRequest":
        if self.offer_type == "deal" and self.sale_price is None:
            raise ValueError("deal submissions require salePrice")
        if self.offer_type == "auction" and self.current_price is None:
            raise ValueError("auction submissions require currentPrice")
        return self


class SubmissionReviewRequest(BaseModel):
    action: SubmissionReviewAction
    target_product_id: str | None = Field(default=None, alias="targetProductId", max_length=36)
    resolution_note: str | None = Field(default=None, alias="resolutionNote", max_length=2000)


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    offer_type: str = Field(alias="offerType")
    source_url: str = Field(alias="sourceUrl")
    product_name: str = Field(alias="productName")
    brand: str | None
    model_name: str | None = Field(alias="modelName")
    category: str | None
    title: str
    seller: str | None
    original_price: int | None = Field(alias="originalPrice")
    sale_price: int | None = Field(alias="salePrice")
    current_price: int | None = Field(alias="currentPrice")
    currency: str
    description: str | None
    status: str
    ai_decision: str | None = Field(alias="aiDecision")
    ai_reason: str | None = Field(alias="aiReason")
    ai_reviewed_at: datetime | None = Field(alias="aiReviewedAt")
    reviewed_by_user_id: str | None = Field(alias="reviewedByUserId")
    resolution_note: str | None = Field(alias="resolutionNote")
    resolved_at: datetime | None = Field(alias="resolvedAt")
    published_product_id: str | None = Field(alias="publishedProductId")
    published_offer_type: str | None = Field(alias="publishedOfferType")
    published_offer_id: str | None = Field(alias="publishedOfferId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer(
        "ai_reviewed_at",
        "resolved_at",
        "created_at",
        "updated_at",
    )
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class SubmissionListResponse(BaseModel):
    items: list[SubmissionResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class ProductMatchResponse(BaseModel):
    product_id: str = Field(alias="productId")
    name: str
    brand: str | None
    model_name: str | None = Field(alias="modelName")
    category: str | None
    score: int
    matched_reasons: list[str] = Field(alias="matchedReasons")


class ProductMatchListResponse(BaseModel):
    items: list[ProductMatchResponse]
