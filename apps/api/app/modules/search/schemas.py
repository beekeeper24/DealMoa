from pydantic import BaseModel, ConfigDict, Field


class ProductSearchItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    brand: str | None = None
    model_name: str | None = Field(default=None, alias="modelName")
    category: str | None = None
    specs_text: str | None = Field(default=None, alias="specsText")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    score: float


class DealSearchItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    title: str
    source_url: str = Field(alias="sourceUrl")
    seller: str | None = None
    original_price: int | None = Field(default=None, alias="originalPrice")
    sale_price: int = Field(alias="salePrice")
    currency: str
    status: str
    started_at: str | None = Field(default=None, alias="startedAt")
    ended_at: str | None = Field(default=None, alias="endedAt")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    score: float


class AuctionSearchItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    product_id: str = Field(alias="productId")
    title: str
    source_url: str = Field(alias="sourceUrl")
    seller: str | None = None
    current_price: int = Field(alias="currentPrice")
    bid_count: int = Field(alias="bidCount")
    currency: str
    status: str
    ends_at: str | None = Field(default=None, alias="endsAt")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    score: float


class ProductSearchResponse(BaseModel):
    items: list[ProductSearchItem]
    next_cursor: str | None = Field(alias="nextCursor")


class DealSearchResponse(BaseModel):
    items: list[DealSearchItem]
    next_cursor: str | None = Field(alias="nextCursor")


class AuctionSearchResponse(BaseModel):
    items: list[AuctionSearchItem]
    next_cursor: str | None = Field(alias="nextCursor")


class SearchReindexResponse(BaseModel):
    products: int
    deals: int
    auctions: int

