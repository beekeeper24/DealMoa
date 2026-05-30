from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import DealNotFoundException, ForbiddenException
from app.db.base import Base
from app.modules.admin.models import AdminAuditLog
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import OfferStatusUpdateRequest
from app.modules.admin.use_cases import AdminUseCases
from app.modules.auth.models import User
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 2, 30, tzinfo=UTC)


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


def seed_offer_data(session: Session) -> None:
    session.add_all(
        [
            User(
                id="admin-1",
                email="admin@example.com",
                nickname="Admin",
                role="ADMIN",
                created_at=NOW,
                updated_at=NOW,
            ),
            Product(
                id="product-1",
                name="Galaxy S26",
                brand="Samsung",
                model_name="SM-S260",
                category="smartphone",
                specs=None,
                created_at=NOW,
                updated_at=NOW,
            ),
            Deal(
                id="deal-1",
                product_id="product-1",
                title="Galaxy S26 launch deal",
                source_url="https://example.com/deals/galaxy-s26",
                seller="Example",
                original_price=None,
                sale_price=1090000,
                currency="KRW",
                status="pending",
                created_at=NOW,
                updated_at=NOW,
            ),
            Auction(
                id="auction-1",
                product_id="product-1",
                title="Galaxy S26 sealed auction",
                source_url="https://example.com/auctions/galaxy-s26",
                seller="Example",
                current_price=720000,
                bid_count=3,
                currency="KRW",
                status="pending",
                created_at=NOW,
                updated_at=NOW,
            ),
        ]
    )
    session.flush()


def make_use_cases(session: Session) -> AdminUseCases:
    return AdminUseCases(
        admin_repository=AdminRepository(session),
        product_repository=ProductRepository(session),
        domain_events=DomainEventsUseCases(
            repository=DomainEventsRepository(session),
            now=lambda: NOW,
        ),
        now=lambda: NOW,
    )


def admin_user(role: str = "ADMIN") -> AuthenticatedUser:
    return AuthenticatedUser(
        id="admin-1",
        email="admin@example.com",
        nickname="Admin",
        role=role,
    )


def test_non_admin_cannot_change_offer_status() -> None:
    session = next(make_session())
    seed_offer_data(session)

    with pytest.raises(ForbiddenException):
        make_use_cases(session).update_deal_status(
            actor=admin_user(role="USER"),
            deal_id="deal-1",
            request=OfferStatusUpdateRequest(status="active", reason="approved"),
        )


def test_admin_changes_deal_status_and_records_audit_log_and_event() -> None:
    session = next(make_session())
    seed_offer_data(session)

    result = make_use_cases(session).update_deal_status(
        actor=admin_user(),
        deal_id="deal-1",
        request=OfferStatusUpdateRequest(status="active", reason="manual approval"),
    )

    audit_log = session.scalar(select(AdminAuditLog))
    event = session.scalar(select(DomainEvent))
    deal = session.get(Deal, "deal-1")
    assert deal is not None
    assert audit_log is not None
    assert event is not None
    assert result.status == "active"
    assert result.previous_status == "pending"
    assert result.audit_log_id == audit_log.id
    assert deal.status == "active"
    assert deal.updated_at.replace(tzinfo=UTC) == NOW
    assert audit_log.actor_user_id == "admin-1"
    assert audit_log.action == "deal.status.changed"
    assert audit_log.target_type == "deal"
    assert audit_log.target_id == "deal-1"
    assert audit_log.previous_status == "pending"
    assert audit_log.new_status == "active"
    assert audit_log.reason == "manual approval"
    assert event.event_type == "deal.status.changed"
    assert event.aggregate_type == "deal"
    assert event.aggregate_id == "deal-1"
    assert event.payload_json["previousStatus"] == "pending"
    assert event.payload_json["newStatus"] == "active"
    assert event.payload_json["actorUserId"] == "admin-1"


def test_admin_changes_auction_status_and_records_audit_log_and_event() -> None:
    session = next(make_session())
    seed_offer_data(session)

    result = make_use_cases(session).update_auction_status(
        actor=admin_user(),
        auction_id="auction-1",
        request=OfferStatusUpdateRequest(status="rejected", reason="duplicate listing"),
    )

    audit_log = session.scalar(select(AdminAuditLog))
    event = session.scalar(select(DomainEvent))
    auction = session.get(Auction, "auction-1")
    assert auction is not None
    assert audit_log is not None
    assert event is not None
    assert result.target_type == "auction"
    assert result.status == "rejected"
    assert result.previous_status == "pending"
    assert auction.status == "rejected"
    assert audit_log.action == "auction.status.changed"
    assert audit_log.target_type == "auction"
    assert audit_log.target_id == "auction-1"
    assert audit_log.new_status == "rejected"
    assert event.event_type == "auction.status.changed"
    assert event.aggregate_type == "auction"
    assert event.aggregate_id == "auction-1"
    assert event.payload_json["newStatus"] == "rejected"


def test_missing_deal_status_update_raises_not_found() -> None:
    session = next(make_session())
    seed_offer_data(session)

    with pytest.raises(DealNotFoundException):
        make_use_cases(session).update_deal_status(
            actor=admin_user(),
            deal_id="missing-deal",
            request=OfferStatusUpdateRequest(status="active", reason=None),
        )
