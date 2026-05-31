from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.search.schemas import (
    AuctionSearchResponse,
    DealSearchResponse,
    ProductSearchResponse,
)

AiSearchTargetType = Literal["products", "deals", "auctions"]
PurchaseRecommendation = Literal["buy", "watch", "avoid"]


class SearchIntentFilters(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str | None = None
    max_price: int | None = Field(default=None, alias="maxPrice")


class SearchIntent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    normalized_query: str = Field(alias="normalizedQuery")
    target_types: list[AiSearchTargetType] = Field(alias="targetTypes")
    filters: SearchIntentFilters


class AiSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=10)


class AiSearchResponse(BaseModel):
    intent: SearchIntent
    summary: str
    products: ProductSearchResponse
    deals: DealSearchResponse
    auctions: AuctionSearchResponse


class PurchaseCheckEvidence(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    label: str
    value: str
    source_type: str | None = Field(default=None, alias="sourceType")
    source_id: str | None = Field(default=None, alias="sourceId")


class ProductPurchaseCheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(alias="productId")
    recommendation: PurchaseRecommendation
    confidence: float
    summary: str
    evidence: list[PurchaseCheckEvidence]
