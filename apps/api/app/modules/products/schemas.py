from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=120)
    model_name: str | None = Field(default=None, alias="modelName", max_length=120)
    category: str | None = Field(default=None, max_length=120)
    specs: dict[str, Any] | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    brand: str | None
    model_name: str | None = Field(alias="modelName")
    category: str | None
    specs: dict[str, Any] | None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("created_at", "updated_at")
    def serialize_timestamps(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class ProductListResponse(BaseModel):
    items: list[ProductResponse]


class DealCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_url: str = Field(alias="sourceUrl")
    seller: str | None = Field(default=None, max_length=120)
    original_price: int | None = Field(default=None, alias="originalPrice", ge=0)
    sale_price: int = Field(alias="salePrice", ge=0)
    currency: str = Field(default="KRW", min_length=3, max_length=3)
    status: str = Field(default="active", max_length=30)


class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    title: str
    source_url: str = Field(alias="sourceUrl")
    seller: str | None
    original_price: int | None = Field(alias="originalPrice")
    sale_price: int = Field(alias="salePrice")
    currency: str
    status: str
    started_at: datetime | None = Field(alias="startedAt")
    ended_at: datetime | None = Field(alias="endedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("started_at", "ended_at", "created_at", "updated_at")
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class DealListResponse(BaseModel):
    items: list[DealResponse]


class AuctionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_url: str = Field(alias="sourceUrl")
    seller: str | None = Field(default=None, max_length=120)
    current_price: int = Field(alias="currentPrice", ge=0)
    bid_count: int = Field(default=0, alias="bidCount", ge=0)
    currency: str = Field(default="KRW", min_length=3, max_length=3)
    status: str = Field(default="active", max_length=30)


class AuctionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    title: str
    source_url: str = Field(alias="sourceUrl")
    seller: str | None
    current_price: int = Field(alias="currentPrice")
    bid_count: int = Field(alias="bidCount")
    currency: str
    status: str
    ends_at: datetime | None = Field(alias="endsAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_serializer("ends_at", "created_at", "updated_at")
    def serialize_timestamps(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class AuctionListResponse(BaseModel):
    items: list[AuctionResponse]
