from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


class ProductFavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class ProductFavoriteListResponse(BaseModel):
    items: list[ProductFavoriteResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class DealFavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    deal_id: str = Field(alias="dealId")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class DealFavoriteListResponse(BaseModel):
    items: list[DealFavoriteResponse]
    next_cursor: str | None = Field(alias="nextCursor")


class AuctionFavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    auction_id: str = Field(alias="auctionId")
    created_at: datetime = Field(alias="createdAt")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        serialized = serialize_utc_datetime(value)
        assert serialized is not None
        return serialized


class AuctionFavoriteListResponse(BaseModel):
    items: list[AuctionFavoriteResponse]
    next_cursor: str | None = Field(alias="nextCursor")
