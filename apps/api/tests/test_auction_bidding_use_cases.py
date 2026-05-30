from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from app.core.exceptions import (
    AuctionAlreadyEndedException,
    AuctionNotFoundException,
    BidTooLowException,
)
from app.db.base import Base
from app.modules.auth.models import User
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, AuctionBid, Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import AuctionBidCreateRequest
from app.modules.products.use_cases import ProductUseCases
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 29, 9, 0, tzinfo=UTC)


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


def make_use_cases(session: Session) -> ProductUseCases:
    return ProductUseCases(
        ProductRepository(session),
        domain_events=DomainEventsUseCases(
            repository=DomainEventsRepository(session),
            now=lambda: NOW,
        ),
        now=lambda: NOW,
    )


def seed_user_product_and_auction(
    session: Session,
    *,
    auction_status: str = "active",
    ends_at: datetime | None = None,
) -> None:
    session.add(
        User(
            id="user-1",
            email="user@example.com",
            nickname="Deal User",
            role="USER",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.add(
        Product(
            id="product-1",
            name="Galaxy S26",
            brand="Samsung",
            model_name="SM-S260",
            category="smartphone",
            specs=None,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.add(
        Auction(
            id="auction-1",
            product_id="product-1",
            title="Galaxy S26 sealed auction",
            source_url="https://example.com/auctions/galaxy-s26",
            seller="Auction House",
            current_price=720000,
            bid_count=3,
            currency="KRW",
            status=auction_status,
            ends_at=ends_at,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.flush()


def test_place_auction_bid_records_bid_and_updates_auction_summary() -> None:
    session = next(make_session())
    seed_user_product_and_auction(session)

    bid = make_use_cases(session).place_auction_bid(
        user_id="user-1",
        auction_id="auction-1",
        request=AuctionBidCreateRequest(amount=750000),
    )

    auction = session.get_one(Auction, "auction-1")
    stored_bid = session.scalars(select(AuctionBid)).one()
    assert bid.id == stored_bid.id
    assert stored_bid.auction_id == "auction-1"
    assert stored_bid.user_id == "user-1"
    assert stored_bid.amount == 750000
    assert auction.current_price == 750000
    assert auction.bid_count == 4
    assert auction.updated_at.replace(tzinfo=UTC) == NOW


def test_place_auction_bid_writes_outbox_event() -> None:
    session = next(make_session())
    seed_user_product_and_auction(session)

    make_use_cases(session).place_auction_bid(
        user_id="user-1",
        auction_id="auction-1",
        request=AuctionBidCreateRequest(amount=750000),
    )

    event = session.scalars(select(DomainEvent)).one()
    assert event.event_type == "auction.bid.placed"
    assert event.aggregate_type == "auction"
    assert event.aggregate_id == "auction-1"
    assert event.payload_json["auctionId"] == "auction-1"
    assert event.payload_json["userId"] == "user-1"
    assert event.payload_json["amount"] == 750000
    assert event.payload_json["currentPrice"] == 750000
    assert event.payload_json["bidCount"] == 4
    assert event.payload_json["previousHighestBidderUserId"] is None


def test_place_auction_bid_records_previous_highest_bidder_in_outbox_event() -> None:
    session = next(make_session())
    seed_user_product_and_auction(session)
    session.add(
        User(
            id="user-2",
            email="user-2@example.com",
            nickname="Deal User 2",
            role="USER",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.add(
        AuctionBid(
            id="bid-previous",
            auction_id="auction-1",
            user_id="user-1",
            amount=720000,
            created_at=NOW,
            updated_at=NOW,
        )
    )

    make_use_cases(session).place_auction_bid(
        user_id="user-2",
        auction_id="auction-1",
        request=AuctionBidCreateRequest(amount=750000),
    )

    event = session.scalars(select(DomainEvent)).one()
    assert event.payload_json["userId"] == "user-2"
    assert event.payload_json["previousHighestBidderUserId"] == "user-1"


def test_place_auction_bid_rejects_low_amount() -> None:
    session = next(make_session())
    seed_user_product_and_auction(session)

    with pytest.raises(BidTooLowException) as exc_info:
        make_use_cases(session).place_auction_bid(
            user_id="user-1",
            auction_id="auction-1",
            request=AuctionBidCreateRequest(amount=720000),
        )

    assert exc_info.value.error_code.code == "BID_TOO_LOW"
    assert exc_info.value.details == {
        "auctionId": "auction-1",
        "currentPrice": 720000,
        "bidAmount": 720000,
        "minimumBidAmount": 721000,
        "bidIncrement": 1000,
    }
    assert session.scalars(select(AuctionBid)).all() == []


def test_place_auction_bid_requires_fixed_minimum_increment() -> None:
    session = next(make_session())
    seed_user_product_and_auction(session)

    with pytest.raises(BidTooLowException) as exc_info:
        make_use_cases(session).place_auction_bid(
            user_id="user-1",
            auction_id="auction-1",
            request=AuctionBidCreateRequest(amount=720999),
        )

    assert exc_info.value.error_code.code == "BID_TOO_LOW"
    assert exc_info.value.details == {
        "auctionId": "auction-1",
        "currentPrice": 720000,
        "bidAmount": 720999,
        "minimumBidAmount": 721000,
        "bidIncrement": 1000,
    }
    assert session.scalars(select(AuctionBid)).all() == []


def test_place_auction_bid_rejects_inactive_or_ended_auction() -> None:
    session = next(make_session())
    seed_user_product_and_auction(
        session,
        auction_status="active",
        ends_at=NOW - timedelta(minutes=1),
    )

    with pytest.raises(AuctionAlreadyEndedException) as exc_info:
        make_use_cases(session).place_auction_bid(
            user_id="user-1",
            auction_id="auction-1",
            request=AuctionBidCreateRequest(amount=750000),
        )

    assert exc_info.value.error_code.code == "AUCTION_ALREADY_ENDED"
    assert exc_info.value.details["auctionId"] == "auction-1"
    assert session.get_one(Auction, "auction-1").current_price == 720000


def test_place_auction_bid_rejects_missing_auction() -> None:
    session = next(make_session())

    with pytest.raises(AuctionNotFoundException):
        make_use_cases(session).place_auction_bid(
            user_id="user-1",
            auction_id="missing-auction",
            request=AuctionBidCreateRequest(amount=750000),
        )
