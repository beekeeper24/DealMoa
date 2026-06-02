from typing import Literal, cast
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError

CrawlerSourceAction = Literal["allow", "block"]
CrawlerSourceReputation = Literal["trusted", "standard", "low"]


class CrawlerSourceProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str = Field(min_length=1)
    reputation: CrawlerSourceReputation
    action: CrawlerSourceAction


class CrawlerRawItem(BaseModel):
    offer_type: Literal["deal", "auction"] = Field(alias="offerType")
    source_url: str = Field(alias="sourceUrl", min_length=1)
    product_name: str = Field(alias="productName", min_length=1)
    brand: str | None = None
    model_name: str | None = Field(default=None, alias="modelName")
    category: str | None = None
    title: str = Field(min_length=1)
    seller: str | None = None
    original_price: int | None = Field(default=None, alias="originalPrice", ge=0)
    sale_price: int | None = Field(default=None, alias="salePrice", ge=0)
    current_price: int | None = Field(default=None, alias="currentPrice", ge=0)
    currency: str = Field(default="KRW", min_length=3, max_length=3)


class CrawlerSourceRegistry:
    def __init__(self, profiles: list[CrawlerSourceProfile]) -> None:
        self.profiles_by_host = {profile.host.casefold(): profile for profile in profiles}

    def parse(self, item: CrawlerRawItem) -> dict[str, object] | None:
        host = urlparse(item.source_url).netloc.casefold()
        profile = self.profiles_by_host.get(host)
        if profile is None or profile.action == "block":
            return None
        return {
            "offerType": item.offer_type,
            "sourceUrl": item.source_url,
            "productName": item.product_name,
            "brand": item.brand,
            "modelName": item.model_name,
            "category": item.category,
            "title": item.title,
            "seller": item.seller,
            "originalPrice": item.original_price,
            "salePrice": item.sale_price,
            "currentPrice": item.current_price,
            "currency": item.currency,
            "description": f"Crawler source reputation: {profile.reputation}",
        }


def parse_source_profiles(value: str) -> list[CrawlerSourceProfile]:
    profiles: list[CrawlerSourceProfile] = []
    for raw_entry in [entry.strip() for entry in value.split(",") if entry.strip()]:
        parts = [part.strip() for part in raw_entry.split(":")]
        if len(parts) != 3:
            raise ValidationError.from_exception_data(
                "CrawlerSourceProfile",
                [
                    {
                        "type": "value_error",
                        "loc": ("sourceProfile",),
                        "input": raw_entry,
                        "ctx": {"error": ValueError("expected host:reputation:action")},
                    }
                ],
            )
        profiles.append(
            CrawlerSourceProfile(
                host=parts[0],
                reputation=cast(CrawlerSourceReputation, parts[1]),
                action=cast(CrawlerSourceAction, parts[2]),
            )
        )
    return profiles
