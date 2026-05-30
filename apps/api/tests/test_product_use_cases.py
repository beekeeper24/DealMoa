from datetime import UTC, datetime
from typing import Any, cast

import pytest
from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    InvalidSearchCursorException,
    ProductNotFoundException,
)
from app.modules.events.models import DomainEvent
from app.modules.products.models import Auction, AuctionView
from app.modules.products.repository import ProductRepository
from app.modules.products.use_cases import ProductUseCases


class EmptyProductRepository:
    def get_product(self, product_id: str) -> None:
        return None

    def get_deal(self, deal_id: str) -> None:
        return None

    def get_auction(self, auction_id: str) -> None:
        return None


class CursorRejectingRepository:
    def get_product(self, product_id: str) -> None:
        return None

    def list_products(self, *, limit: int, cursor: str | None) -> object:
        raise InvalidSearchCursorException(cursor or "")


class RecordingAuctionViewRepository:
    def __init__(self) -> None:
        self.auction = Auction(
            id="auction-1",
            product_id="product-1",
            title="Galaxy S26 sealed auction",
            source_url="https://example.com/auctions/galaxy-s26",
            seller="Auction House",
            current_price=720000,
            bid_count=3,
            currency="KRW",
            status="active",
            created_at=datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
        )
        self.views: list[AuctionView] = []

    def get_auction(self, auction_id: str) -> Auction | None:
        if auction_id == self.auction.id:
            return self.auction
        return None

    def create_auction_view(self, view: AuctionView) -> AuctionView:
        self.views.append(view)
        return view


class RecordingDomainEvents:
    def __init__(self) -> None:
        self.auction_view_events: list[AuctionView] = []

    def record_auction_view_recorded(self, view: AuctionView) -> DomainEvent | None:
        self.auction_view_events.append(view)
        return None


def test_get_product_raises_domain_exception_for_missing_product() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, EmptyProductRepository()))

    with pytest.raises(ProductNotFoundException) as exc_info:
        use_cases.get_product("missing-product")

    assert exc_info.value.error_code.code == "PRODUCT_NOT_FOUND"
    assert exc_info.value.details == {"productId": "missing-product"}


def test_list_products_raises_domain_exception_for_invalid_cursor() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, CursorRejectingRepository()))

    with pytest.raises(InvalidSearchCursorException) as exc_info:
        use_cases.list_products(limit=20, cursor="bad-cursor")

    assert exc_info.value.error_code.code == "INVALID_SEARCH_CURSOR"
    assert exc_info.value.details == {"cursor": "bad-cursor"}


def test_get_deal_raises_domain_exception_for_missing_deal() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, EmptyProductRepository()))

    with pytest.raises(DealNotFoundException) as exc_info:
        use_cases.get_deal("missing-deal")

    assert exc_info.value.error_code.code == "DEAL_NOT_FOUND"
    assert exc_info.value.details == {"dealId": "missing-deal"}


def test_get_auction_raises_domain_exception_for_missing_auction() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, EmptyProductRepository()))

    with pytest.raises(AuctionNotFoundException) as exc_info:
        use_cases.get_auction("missing-auction")

    assert exc_info.value.error_code.code == "AUCTION_NOT_FOUND"
    assert exc_info.value.details == {"auctionId": "missing-auction"}


def test_view_auction_records_view_and_outbox_event() -> None:
    repository = RecordingAuctionViewRepository()
    domain_events = RecordingDomainEvents()
    now = datetime(2026, 5, 31, 13, 0, tzinfo=UTC)
    use_cases = ProductUseCases(
        cast(ProductRepository, repository),
        domain_events=cast(Any, domain_events),
        now=lambda: now,
    )

    viewed = use_cases.view_auction("auction-1")

    assert viewed.id == "auction-1"
    assert len(repository.views) == 1
    assert repository.views[0].auction_id == "auction-1"
    assert repository.views[0].created_at == now
    assert domain_events.auction_view_events == repository.views
