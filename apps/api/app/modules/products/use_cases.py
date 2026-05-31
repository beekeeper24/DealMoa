from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import (
    AuctionAlreadyEndedException,
    AuctionNotFoundException,
    BidTooLowException,
    DealNotFoundException,
    ProductNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.evidence.models import PriceHistorySnapshot
from app.modules.evidence.repository import EvidenceRepository
from app.modules.products.models import Auction, AuctionBid, AuctionView, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    AuctionBidCreateRequest,
    AuctionCreateRequest,
    DealCreateRequest,
    ProductCreateRequest,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


AUCTION_BID_INCREMENT = 1000


class ProductUseCases:
    def __init__(
        self,
        repository: ProductRepository,
        domain_events: DomainEventsUseCases | None = None,
        evidence_repository: EvidenceRepository | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.domain_events = domain_events
        self.evidence_repository = evidence_repository
        self.now = now or utc_now

    def create_product(self, request: ProductCreateRequest) -> Product:
        now = self.now()
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
        now = self.now()
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
        self._record_price_snapshot(
            product_id=created.product_id,
            source_type="deal",
            source_id=created.id,
            price=created.sale_price,
            currency=created.currency,
            observed_at=now,
        )
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
        now = self.now()
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
        self._record_price_snapshot(
            product_id=created.product_id,
            source_type="auction",
            source_id=created.id,
            price=created.current_price,
            currency=created.currency,
            observed_at=now,
        )
        if self.domain_events is not None:
            self.domain_events.record_auction_created(created)
        return created

    def get_auction(self, auction_id: str) -> Auction:
        auction = self.repository.get_auction(auction_id)
        if auction is None:
            raise AuctionNotFoundException(auction_id)
        return auction

    def view_auction(self, auction_id: str) -> Auction:
        auction = self.get_auction(auction_id)
        now = self.now()
        view = self.repository.create_auction_view(
            AuctionView(
                auction_id=auction.id,
                created_at=now,
                updated_at=now,
            )
        )
        if self.domain_events is not None:
            self.domain_events.record_auction_view_recorded(view)
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

    def place_auction_bid(
        self,
        *,
        user_id: str,
        auction_id: str,
        request: AuctionBidCreateRequest,
    ) -> AuctionBid:
        auction = self.repository.get_auction_for_update(auction_id)
        if auction is None:
            raise AuctionNotFoundException(auction_id)

        now = self.now()
        if auction.status != "active" or (
            auction.ends_at is not None and self._aware_utc(auction.ends_at) <= now
        ):
            raise AuctionAlreadyEndedException(
                auction_id=auction.id,
                status=auction.status,
                ends_at=self._serialize_datetime(auction.ends_at),
            )

        if request.amount < auction.current_price + AUCTION_BID_INCREMENT:
            raise BidTooLowException(
                auction_id=auction.id,
                current_price=auction.current_price,
                bid_amount=request.amount,
                bid_increment=AUCTION_BID_INCREMENT,
            )

        previous_highest_bid = self.repository.get_highest_auction_bid(auction.id)
        bid = self.repository.create_auction_bid(
            AuctionBid(
                auction_id=auction.id,
                user_id=user_id,
                amount=request.amount,
                created_at=now,
                updated_at=now,
            )
        )
        auction.current_price = request.amount
        auction.bid_count += 1
        auction.updated_at = now
        self._record_price_snapshot(
            product_id=auction.product_id,
            source_type="auction",
            source_id=auction.id,
            price=auction.current_price,
            currency=auction.currency,
            observed_at=now,
        )
        if self.domain_events is not None:
            self.domain_events.record_auction_bid_placed(
                auction=auction,
                bid=bid,
                previous_highest_bidder_user_id=(
                    previous_highest_bid.user_id if previous_highest_bid is not None else None
                ),
            )
        return bid

    def _record_price_snapshot(
        self,
        *,
        product_id: str,
        source_type: str,
        source_id: str,
        price: int,
        currency: str,
        observed_at: datetime,
    ) -> None:
        if self.evidence_repository is None:
            return
        now = self.now()
        self.evidence_repository.create_price_snapshot(
            PriceHistorySnapshot(
                product_id=product_id,
                source_type=source_type,
                source_id=source_id,
                price=price,
                currency=currency,
                observed_at=observed_at,
                created_at=now,
                updated_at=now,
            )
        )

    def _aware_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return self._aware_utc(value).isoformat().replace("+00:00", "Z")
