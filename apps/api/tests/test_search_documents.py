from datetime import UTC, datetime

from app.modules.products.models import Auction, AuctionBid, Deal, Product
from app.modules.search.documents import (
    build_auction_document,
    build_deal_document,
    build_product_document,
)


def test_product_search_document_flattens_specs_for_text_search() -> None:
    product = Product(
        id="product-1",
        name="Galaxy S26 Ultra",
        brand="Samsung",
        model_name="SM-S260",
        category="smartphone",
        specs={"storage": "256GB", "색상": "블랙"},
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
        updated_at=datetime(2026, 5, 25, tzinfo=UTC),
    )

    document = build_product_document(product)

    assert document["id"] == "product-1"
    assert document["name"] == "Galaxy S26 Ultra"
    assert document["brand"] == "Samsung"
    assert document["modelName"] == "SM-S260"
    assert document["category"] == "smartphone"
    assert document["specsText"] == "storage 256GB 색상 블랙"
    assert document["createdAt"] == "2026-05-25T00:00:00Z"
    assert document["updatedAt"] == "2026-05-25T00:00:00Z"


def test_deal_search_document_keeps_product_and_price_fields() -> None:
    deal = Deal(
        id="deal-1",
        product_id="product-1",
        title="Galaxy S26 launch deal",
        source_url="https://example.com/deals/galaxy-s26",
        seller="Example Store",
        original_price=1400000,
        sale_price=1090000,
        currency="KRW",
        status="active",
        started_at=None,
        ended_at=None,
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
        updated_at=datetime(2026, 5, 25, tzinfo=UTC),
    )

    document = build_deal_document(deal)

    assert document["id"] == "deal-1"
    assert document["productId"] == "product-1"
    assert document["salePrice"] == 1090000
    assert document["status"] == "active"
    assert document["createdAt"] == "2026-05-25T00:00:00Z"


def test_auction_search_document_keeps_activity_fields() -> None:
    auction = Auction(
        id="auction-1",
        product_id="product-1",
        title="Galaxy S26 sealed auction",
        source_url="https://example.com/auctions/galaxy-s26",
        seller="Auction House",
        current_price=720000,
        bid_count=3,
        currency="KRW",
        status="active",
        ends_at=datetime(2026, 5, 26, tzinfo=UTC),
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
        updated_at=datetime(2026, 5, 25, tzinfo=UTC),
    )

    document = build_auction_document(auction)

    assert document["id"] == "auction-1"
    assert document["productId"] == "product-1"
    assert document["currentPrice"] == 720000
    assert document["bidCount"] == 3
    assert document["endsAt"] == "2026-05-26T00:00:00Z"


def test_auction_search_document_counts_unique_bidders() -> None:
    auction = Auction(
        id="auction-1",
        product_id="product-1",
        title="Galaxy S26 sealed auction",
        source_url="https://example.com/auctions/galaxy-s26",
        seller="Auction House",
        current_price=780000,
        bid_count=3,
        currency="KRW",
        status="active",
        ends_at=datetime(2026, 5, 26, tzinfo=UTC),
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
        updated_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    auction.bids = [
        AuctionBid(
            id="bid-1",
            auction_id="auction-1",
            user_id="user-1",
            amount=740000,
            created_at=datetime(2026, 5, 25, tzinfo=UTC),
            updated_at=datetime(2026, 5, 25, tzinfo=UTC),
        ),
        AuctionBid(
            id="bid-2",
            auction_id="auction-1",
            user_id="user-1",
            amount=760000,
            created_at=datetime(2026, 5, 25, tzinfo=UTC),
            updated_at=datetime(2026, 5, 25, tzinfo=UTC),
        ),
        AuctionBid(
            id="bid-3",
            auction_id="auction-1",
            user_id="user-2",
            amount=780000,
            created_at=datetime(2026, 5, 25, tzinfo=UTC),
            updated_at=datetime(2026, 5, 25, tzinfo=UTC),
        ),
    ]

    document = build_auction_document(auction)

    assert document["uniqueBidderCount"] == 2
