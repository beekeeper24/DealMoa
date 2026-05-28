from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 14, 0, tzinfo=UTC)


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


def make_use_cases(session: Session) -> DomainEventsUseCases:
    return DomainEventsUseCases(repository=DomainEventsRepository(session), now=lambda: NOW)


def test_record_product_updated_event() -> None:
    session = next(make_session())
    product = Product(
        id="product-1",
        name="Galaxy S26",
        brand="Samsung",
        model_name="SM-S260",
        category="smartphone",
        specs={"storage": "256GB"},
        created_at=NOW,
        updated_at=NOW,
    )

    event = make_use_cases(session).record_product_updated(product)

    stored = session.scalars(select(DomainEvent)).one()
    assert event.id == stored.id
    assert stored.event_type == "product.updated"
    assert stored.aggregate_type == "product"
    assert stored.aggregate_id == "product-1"
    assert stored.payload_json == {
        "productId": "product-1",
        "name": "Galaxy S26",
        "brand": "Samsung",
        "modelName": "SM-S260",
        "category": "smartphone",
        "specs": {"storage": "256GB"},
    }


def test_record_deal_created_event() -> None:
    session = next(make_session())
    deal = Deal(
        id="deal-1",
        product_id="product-1",
        title="Galaxy S26 launch deal",
        source_url="https://example.com/deals/1",
        seller="Example",
        original_price=1400000,
        sale_price=1090000,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )

    make_use_cases(session).record_deal_created(deal)

    stored = session.scalars(select(DomainEvent)).one()
    assert stored.event_type == "deal.created"
    assert stored.aggregate_type == "deal"
    assert stored.aggregate_id == "deal-1"
    assert stored.payload_json["dealId"] == "deal-1"
    assert stored.payload_json["productId"] == "product-1"
    assert stored.payload_json["salePrice"] == 1090000


def test_record_auction_created_event() -> None:
    session = next(make_session())
    auction = Auction(
        id="auction-1",
        product_id="product-1",
        title="Galaxy S26 sealed auction",
        source_url="https://example.com/auctions/1",
        seller="Example",
        current_price=720000,
        bid_count=3,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )

    make_use_cases(session).record_auction_created(auction)

    stored = session.scalars(select(DomainEvent)).one()
    assert stored.event_type == "auction.created"
    assert stored.aggregate_type == "auction"
    assert stored.aggregate_id == "auction-1"
    assert stored.payload_json["auctionId"] == "auction-1"
    assert stored.payload_json["productId"] == "product-1"
    assert stored.payload_json["currentPrice"] == 720000
