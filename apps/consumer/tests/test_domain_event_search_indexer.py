from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from app.db.base import Base
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.search.indexes import SearchIndexKind
from consumer_app.domain_events import DomainEventSearchIndexer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 16, 0, tzinfo=UTC)


class RecordingSearchClient:
    def __init__(self) -> None:
        self.indexed: list[tuple[SearchIndexKind, dict[str, Any]]] = []

    def recreate_indexes(self) -> None:
        raise AssertionError("event indexer should not recreate indexes")

    def replace_documents(
        self,
        kind: SearchIndexKind,
        documents: list[dict[str, Any]],
    ) -> None:
        raise AssertionError("event indexer should not bulk replace documents")

    def index_document(self, kind: SearchIndexKind, document: dict[str, Any]) -> None:
        self.indexed.append((kind, document))

    def search(
        self,
        kind: SearchIndexKind,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> Any:
        raise AssertionError("event indexer should not search")

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> Any:
        raise AssertionError("event indexer should not rank auctions")


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def seed_product(session: Session) -> None:
    session.add(
        Product(
            id="product-1",
            name="Galaxy S26",
            brand="Samsung",
            model_name="SM-S260",
            category="smartphone",
            specs={"storage": "256GB"},
            created_at=NOW,
            updated_at=NOW,
        )
    )


def seed_deal(session: Session) -> None:
    session.add(
        Deal(
            id="deal-1",
            product_id="product-1",
            title="Galaxy S26 launch deal",
            source_url="https://example.com/deals/galaxy-s26",
            seller="Example",
            original_price=None,
            sale_price=1090000,
            currency="KRW",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def seed_auction(session: Session) -> None:
    session.add(
        Auction(
            id="auction-1",
            product_id="product-1",
            title="Galaxy S26 sealed auction",
            source_url="https://example.com/auctions/galaxy-s26",
            seller="Example",
            current_price=720000,
            bid_count=3,
            currency="KRW",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def make_indexer(
    session: Session,
    search_client: RecordingSearchClient,
) -> DomainEventSearchIndexer:
    return DomainEventSearchIndexer(
        product_repository=ProductRepository(session),
        search_client=search_client,
    )


def test_handle_product_updated_indexes_product_document() -> None:
    session = next(make_session())
    seed_product(session)
    search_client = RecordingSearchClient()

    handled = make_indexer(session, search_client).handle(
        {
            "eventId": "event-1",
            "eventType": "product.updated",
            "aggregateType": "product",
            "aggregateId": "product-1",
            "payload": {"productId": "product-1"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )

    assert handled is True
    assert search_client.indexed[0][0] == "products"
    assert search_client.indexed[0][1]["id"] == "product-1"
    assert search_client.indexed[0][1]["specsText"] == "storage 256GB"


def test_handle_deal_and_auction_created_indexes_offer_documents() -> None:
    session = next(make_session())
    seed_product(session)
    seed_deal(session)
    seed_auction(session)
    search_client = RecordingSearchClient()
    indexer = make_indexer(session, search_client)

    deal_handled = indexer.handle(
        {
            "eventId": "event-2",
            "eventType": "deal.created",
            "aggregateType": "deal",
            "aggregateId": "deal-1",
            "payload": {"dealId": "deal-1"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )
    auction_handled = indexer.handle(
        {
            "eventId": "event-3",
            "eventType": "auction.created",
            "aggregateType": "auction",
            "aggregateId": "auction-1",
            "payload": {"auctionId": "auction-1"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )

    assert deal_handled is True
    assert auction_handled is True
    assert [kind for kind, _document in search_client.indexed] == ["deals", "auctions"]
    assert search_client.indexed[0][1]["salePrice"] == 1090000
    assert search_client.indexed[1][1]["currentPrice"] == 720000


def test_handle_auction_bid_placed_refreshes_auction_document() -> None:
    session = next(make_session())
    seed_product(session)
    seed_auction(session)
    auction = session.get(Auction, "auction-1")
    assert auction is not None
    auction.current_price = 750000
    auction.bid_count = 4
    search_client = RecordingSearchClient()

    handled = make_indexer(session, search_client).handle(
        {
            "eventId": "event-4",
            "eventType": "auction.bid.placed",
            "aggregateType": "auction",
            "aggregateId": "auction-1",
            "payload": {
                "auctionId": "auction-1",
                "bidId": "bid-1",
                "amount": 750000,
                "currentPrice": 750000,
                "bidCount": 4,
            },
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )

    assert handled is True
    assert search_client.indexed[0][0] == "auctions"
    assert search_client.indexed[0][1]["id"] == "auction-1"
    assert search_client.indexed[0][1]["currentPrice"] == 750000
    assert search_client.indexed[0][1]["bidCount"] == 4


def test_handle_unknown_event_or_missing_aggregate_is_noop() -> None:
    session = next(make_session())
    search_client = RecordingSearchClient()
    indexer = make_indexer(session, search_client)

    unknown_handled = indexer.handle(
        {
            "eventId": "event-4",
            "eventType": "review.verified",
            "aggregateType": "review",
            "aggregateId": "review-1",
            "payload": {"reviewId": "review-1"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )
    missing_handled = indexer.handle(
        {
            "eventId": "event-5",
            "eventType": "product.updated",
            "aggregateType": "product",
            "aggregateId": "missing-product",
            "payload": {"productId": "missing-product"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    )

    assert unknown_handled is False
    assert missing_handled is False
    assert search_client.indexed == []
