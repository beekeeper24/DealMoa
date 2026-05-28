from datetime import UTC, datetime

from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    ProductNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    AuctionCreateRequest,
    DealCreateRequest,
    ProductCreateRequest,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProductUseCases:
    def __init__(
        self,
        repository: ProductRepository,
        domain_events: DomainEventsUseCases | None = None,
    ) -> None:
        self.repository = repository
        self.domain_events = domain_events

    def create_product(self, request: ProductCreateRequest) -> Product:
        now = utc_now()
        product = Product(
            name=request.name,
            brand=request.brand,
            model_name=request.model_name,
            category=request.category,
            specs=request.specs,
            created_at=now,
            updated_at=now,
        )
        created = self.repository.create_product(product)
        if self.domain_events is not None:
            self.domain_events.record_product_updated(created)
        return created

    def get_product(self, product_id: str) -> Product:
        product = self.repository.get_product(product_id)
        if product is None:
            raise ProductNotFoundException(product_id)
        return product

    def list_products(self, *, limit: int, cursor: str | None) -> CursorPage[Product]:
        return self.repository.list_products(limit=limit, cursor=cursor)

    def create_deal(self, product_id: str, request: DealCreateRequest) -> Deal:
        self.get_product(product_id)
        now = utc_now()
        deal = Deal(
            product_id=product_id,
            title=request.title,
            source_url=request.source_url,
            seller=request.seller,
            original_price=request.original_price,
            sale_price=request.sale_price,
            currency=request.currency,
            status=request.status,
            created_at=now,
            updated_at=now,
        )
        created = self.repository.create_deal(deal)
        if self.domain_events is not None:
            self.domain_events.record_deal_created(created)
        return created

    def get_deal(self, deal_id: str) -> Deal:
        deal = self.repository.get_deal(deal_id)
        if deal is None:
            raise DealNotFoundException(deal_id)
        return deal

    def list_deals_for_product(
        self,
        product_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Deal]:
        self.get_product(product_id)
        return self.repository.list_deals_for_product(product_id, limit=limit, cursor=cursor)

    def create_auction(self, product_id: str, request: AuctionCreateRequest) -> Auction:
        self.get_product(product_id)
        now = utc_now()
        auction = Auction(
            product_id=product_id,
            title=request.title,
            source_url=request.source_url,
            seller=request.seller,
            current_price=request.current_price,
            bid_count=request.bid_count,
            currency=request.currency,
            status=request.status,
            created_at=now,
            updated_at=now,
        )
        created = self.repository.create_auction(auction)
        if self.domain_events is not None:
            self.domain_events.record_auction_created(created)
        return created

    def get_auction(self, auction_id: str) -> Auction:
        auction = self.repository.get_auction(auction_id)
        if auction is None:
            raise AuctionNotFoundException(auction_id)
        return auction

    def list_auctions_for_product(
        self,
        product_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Auction]:
        self.get_product(product_id)
        return self.repository.list_auctions_for_product(product_id, limit=limit, cursor=cursor)
