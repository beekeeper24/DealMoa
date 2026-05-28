from datetime import UTC, datetime
from typing import Any

from app.modules.products.models import Auction, Deal, Product

SearchDocument = dict[str, Any]


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


def flatten_specs(specs: dict[str, object] | None) -> str | None:
    if not specs:
        return None
    parts: list[str] = []
    for key, value in specs.items():
        parts.append(str(key))
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for pair in value.items() for item in pair)
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts)


def build_product_document(product: Product) -> SearchDocument:
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "modelName": product.model_name,
        "category": product.category,
        "specsText": flatten_specs(product.specs),
        "createdAt": serialize_datetime(product.created_at),
        "updatedAt": serialize_datetime(product.updated_at),
    }


def build_deal_document(deal: Deal) -> SearchDocument:
    return {
        "id": deal.id,
        "productId": deal.product_id,
        "title": deal.title,
        "sourceUrl": deal.source_url,
        "seller": deal.seller,
        "originalPrice": deal.original_price,
        "salePrice": deal.sale_price,
        "currency": deal.currency,
        "status": deal.status,
        "startedAt": serialize_datetime(deal.started_at),
        "endedAt": serialize_datetime(deal.ended_at),
        "createdAt": serialize_datetime(deal.created_at),
        "updatedAt": serialize_datetime(deal.updated_at),
    }


def build_auction_document(auction: Auction) -> SearchDocument:
    unique_bidder_count = len({bid.user_id for bid in auction.bids})
    return {
        "id": auction.id,
        "productId": auction.product_id,
        "title": auction.title,
        "sourceUrl": auction.source_url,
        "seller": auction.seller,
        "currentPrice": auction.current_price,
        "bidCount": auction.bid_count,
        "uniqueBidderCount": unique_bidder_count,
        "currency": auction.currency,
        "status": auction.status,
        "endsAt": serialize_datetime(auction.ends_at),
        "createdAt": serialize_datetime(auction.created_at),
        "updatedAt": serialize_datetime(auction.updated_at),
    }
