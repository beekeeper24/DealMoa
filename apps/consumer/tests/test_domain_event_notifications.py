from collections.abc import Iterator
from datetime import UTC, datetime

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.favorites.models import ProductFavorite
from app.modules.notifications.models import Notification, NotificationType
from app.modules.products.models import Auction, AuctionBid, Deal, Product
from consumer_app.notification_events import DomainEventNotificationGenerator
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 17, 0, tzinfo=UTC)


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


def add_user(session: Session, user_id: str) -> None:
    session.add(
        User(
            id=user_id,
            email=f"{user_id}@example.com",
            nickname=user_id,
            role="USER",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def seed_product(session: Session, product_id: str = "product-1") -> None:
    session.add(
        Product(
            id=product_id,
            name="Galaxy S26",
            brand="Samsung",
            model_name="SM-S260",
            category="smartphone",
            specs=None,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def add_product_favorite(session: Session, *, user_id: str, product_id: str) -> None:
    session.add(
        ProductFavorite(
            user_id=user_id,
            product_id=product_id,
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


def add_auction_bid(
    session: Session,
    *,
    bid_id: str,
    user_id: str,
    amount: int,
) -> None:
    session.add(
        AuctionBid(
            id=bid_id,
            auction_id="auction-1",
            user_id=user_id,
            amount=amount,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def make_generator(session: Session) -> DomainEventNotificationGenerator:
    return DomainEventNotificationGenerator.from_session(session=session, now=lambda: NOW)


def list_notifications(session: Session) -> list[Notification]:
    return list(session.scalars(select(Notification).order_by(Notification.user_id)))


def test_handle_deal_created_generates_notifications_for_product_favorite_users() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    add_user(session, "user-3")
    seed_product(session, "product-1")
    seed_product(session, "product-2")
    add_product_favorite(session, user_id="user-1", product_id="product-1")
    add_product_favorite(session, user_id="user-2", product_id="product-1")
    add_product_favorite(session, user_id="user-3", product_id="product-2")
    seed_deal(session)

    handled = make_generator(session).handle(
        {
            "eventId": "event-1",
            "eventType": "deal.created",
            "aggregateType": "deal",
            "aggregateId": "deal-1",
            "payload": {"dealId": "deal-1"},
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )

    notifications = list_notifications(session)
    assert handled is True
    assert [notification.user_id for notification in notifications] == ["user-1", "user-2"]
    assert {notification.type for notification in notifications} == {NotificationType.NEW_DEAL}
    assert {notification.target_id for notification in notifications} == {"deal-1"}


def test_handle_auction_created_is_idempotent_for_duplicate_delivery() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    seed_product(session)
    add_product_favorite(session, user_id="user-1", product_id="product-1")
    seed_auction(session)
    generator = make_generator(session)
    envelope = {
        "eventId": "event-2",
        "eventType": "auction.created",
        "aggregateType": "auction",
        "aggregateId": "auction-1",
        "payload": {"auctionId": "auction-1"},
        "occurredAt": "2026-05-28T17:00:00Z",
    }

    first_handled = generator.handle(envelope)
    second_handled = generator.handle(envelope)

    notifications = list_notifications(session)
    assert first_handled is True
    assert second_handled is True
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.NEW_AUCTION
    assert notifications[0].target_id == "auction-1"


def test_handle_auction_bid_placed_notifies_previous_highest_bidder() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    seed_product(session)
    seed_auction(session)
    add_auction_bid(session, bid_id="bid-previous", user_id="user-1", amount=720000)
    generator = make_generator(session)
    envelope = {
        "eventId": "event-3",
        "eventType": "auction.bid.placed",
        "aggregateType": "auction",
        "aggregateId": "auction-1",
        "payload": {
            "auctionId": "auction-1",
            "bidId": "bid-new",
            "userId": "user-2",
            "amount": 750000,
            "currentPrice": 750000,
            "bidCount": 4,
            "previousHighestBidderUserId": "user-1",
        },
        "occurredAt": "2026-05-28T17:00:00Z",
    }

    first_handled = generator.handle(envelope)
    second_handled = generator.handle(envelope)

    notifications = list_notifications(session)
    assert first_handled is True
    assert second_handled is True
    assert len(notifications) == 1
    assert notifications[0].user_id == "user-1"
    assert notifications[0].type == NotificationType.AUCTION_OUTBID
    assert notifications[0].target_type == "auction"
    assert notifications[0].target_id == "auction-1"
    assert notifications[0].metadata_json["amount"] == 750000


def test_handle_auction_bid_placed_ignores_no_notification_cases() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    seed_product(session)
    seed_auction(session)
    generator = make_generator(session)

    first_bid_handled = generator.handle(
        {
            "eventId": "event-4",
            "eventType": "auction.bid.placed",
            "aggregateType": "auction",
            "aggregateId": "auction-1",
            "payload": {
                "auctionId": "auction-1",
                "bidId": "bid-first",
                "userId": "user-1",
                "amount": 721000,
                "previousHighestBidderUserId": None,
            },
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )
    self_outbid_handled = generator.handle(
        {
            "eventId": "event-5",
            "eventType": "auction.bid.placed",
            "aggregateType": "auction",
            "aggregateId": "auction-1",
            "payload": {
                "auctionId": "auction-1",
                "bidId": "bid-self",
                "userId": "user-1",
                "amount": 750000,
                "previousHighestBidderUserId": "user-1",
            },
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )
    invalid_previous_bidder_handled = generator.handle(
        {
            "eventId": "event-6",
            "eventType": "auction.bid.placed",
            "aggregateType": "auction",
            "aggregateId": "auction-1",
            "payload": {
                "auctionId": "auction-1",
                "bidId": "bid-invalid",
                "userId": "user-2",
                "amount": 750000,
                "previousHighestBidderUserId": "user-1",
            },
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )

    assert first_bid_handled is True
    assert self_outbid_handled is True
    assert invalid_previous_bidder_handled is True
    assert list_notifications(session) == []


def test_handle_unknown_event_or_missing_aggregate_is_noop() -> None:
    session = next(make_session())
    generator = make_generator(session)

    unknown_handled = generator.handle(
        {
            "eventId": "event-3",
            "eventType": "product.updated",
            "aggregateType": "product",
            "aggregateId": "product-1",
            "payload": {"productId": "product-1"},
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )
    missing_handled = generator.handle(
        {
            "eventId": "event-4",
            "eventType": "deal.created",
            "aggregateType": "deal",
            "aggregateId": "missing-deal",
            "payload": {"dealId": "missing-deal"},
            "occurredAt": "2026-05-28T17:00:00Z",
        }
    )

    assert unknown_handled is False
    assert missing_handled is False
    assert list_notifications(session) == []
