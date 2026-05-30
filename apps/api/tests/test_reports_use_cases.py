from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import AuctionNotFoundException, DealNotFoundException, ForbiddenException
from app.core.pagination import CursorPage
from app.db.base import Base
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.models import User
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from app.modules.reports.models import OfferReport
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import ReportCreateRequest, ReportReviewRequest
from app.modules.reports.use_cases import ReportsUseCases
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 3, 30, tzinfo=UTC)


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


def seed_data(session: Session) -> None:
    session.add_all(
        [
            User(
                id="user-1",
                email="user@example.com",
                nickname="User",
                role="USER",
                created_at=NOW,
                updated_at=NOW,
            ),
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
                status="active",
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
                status="active",
                created_at=NOW,
                updated_at=NOW,
            ),
        ]
    )
    session.flush()


def make_use_cases(session: Session) -> ReportsUseCases:
    return ReportsUseCases(
        repository=ReportsRepository(session),
        domain_events=DomainEventsUseCases(
            repository=DomainEventsRepository(session),
            now=lambda: NOW,
        ),
        now=lambda: NOW,
    )


def user(role: str = "USER") -> AuthenticatedUser:
    return AuthenticatedUser(
        id="admin-1" if role == "ADMIN" else "user-1",
        email="admin@example.com" if role == "ADMIN" else "user@example.com",
        nickname=role,
        role=role,
    )


def test_user_reports_deal_and_duplicate_open_report_is_idempotent() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)

    first = use_cases.report_deal(
        actor=user(),
        deal_id="deal-1",
        request=ReportCreateRequest(reasonCode="suspicious_price", description="Too cheap"),
    )
    second = use_cases.report_deal(
        actor=user(),
        deal_id="deal-1",
        request=ReportCreateRequest(reasonCode="suspicious_price", description="Too cheap"),
    )

    reports = list(session.scalars(select(OfferReport)))
    assert first.id == second.id
    assert len(reports) == 1
    assert first.user_id == "user-1"
    assert first.target_type == "deal"
    assert first.target_id == "deal-1"
    assert first.reason_code == "suspicious_price"
    assert first.description == "Too cheap"
    assert first.status == "open"


def test_user_reports_auction() -> None:
    session = next(make_session())
    seed_data(session)

    report = make_use_cases(session).report_auction(
        actor=user(),
        auction_id="auction-1",
        request=ReportCreateRequest(reasonCode="external_link_broken", description=None),
    )

    assert report.target_type == "auction"
    assert report.target_id == "auction-1"
    assert report.status == "open"


def test_report_missing_targets_raise_domain_not_found() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)

    with pytest.raises(DealNotFoundException):
        use_cases.report_deal(
            actor=user(),
            deal_id="missing-deal",
            request=ReportCreateRequest(reasonCode="fraud", description=None),
        )
    with pytest.raises(AuctionNotFoundException):
        use_cases.report_auction(
            actor=user(),
            auction_id="missing-auction",
            request=ReportCreateRequest(reasonCode="fraud", description=None),
        )


def test_admin_lists_open_reports_with_cursor_pagination() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)
    deal_report = use_cases.report_deal(
        actor=user(),
        deal_id="deal-1",
        request=ReportCreateRequest(reasonCode="fraud", description=None),
    )
    auction_report = use_cases.report_auction(
        actor=user(),
        auction_id="auction-1",
        request=ReportCreateRequest(reasonCode="broken_link", description=None),
    )

    first_page = use_cases.list_reports(
        actor=user(role="ADMIN"),
        status="open",
        limit=1,
        cursor=None,
    )
    second_page = use_cases.list_reports(
        actor=user(role="ADMIN"),
        status="open",
        limit=1,
        cursor=first_page.next_cursor,
    )

    assert isinstance(first_page, CursorPage)
    assert len(first_page.items) == 1
    assert first_page.next_cursor == first_page.items[0].id
    assert len(second_page.items) == 1
    assert {first_page.items[0].id, second_page.items[0].id} == {
        deal_report.id,
        auction_report.id,
    }
    assert second_page.next_cursor is None


def test_non_admin_cannot_list_or_review_reports() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)

    with pytest.raises(ForbiddenException):
        use_cases.list_reports(actor=user(), status="open", limit=20, cursor=None)
    with pytest.raises(ForbiddenException):
        use_cases.review_report(
            actor=user(),
            report_id="report-1",
            request=ReportReviewRequest(status="resolved", resolutionNote="handled"),
        )


def test_admin_resolves_report_and_records_audit_log() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)
    report = use_cases.report_deal(
        actor=user(),
        deal_id="deal-1",
        request=ReportCreateRequest(reasonCode="fraud", description=None),
    )

    reviewed = use_cases.review_report(
        actor=user(role="ADMIN"),
        report_id=report.id,
        request=ReportReviewRequest(status="resolved", resolutionNote="status changed"),
    )

    audit_log = session.scalar(select(AdminAuditLog))
    assert audit_log is not None
    assert reviewed.status == "resolved"
    assert reviewed.reviewed_by_user_id == "admin-1"
    assert reviewed.resolution_note == "status changed"
    assert reviewed.resolved_at is not None
    assert audit_log.actor_user_id == "admin-1"
    assert audit_log.action == "report.resolved"
    assert audit_log.target_type == "report"
    assert audit_log.target_id == report.id
    assert audit_log.previous_status == "open"
    assert audit_log.new_status == "resolved"


def test_admin_resolves_deal_report_with_target_status_and_records_status_event() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)
    report = use_cases.report_deal(
        actor=user(),
        deal_id="deal-1",
        request=ReportCreateRequest(reasonCode="fraud", description=None),
    )

    reviewed = use_cases.review_report(
        actor=user(role="ADMIN"),
        report_id=report.id,
        request=ReportReviewRequest(
            status="resolved",
            resolutionNote="confirmed fraudulent listing",
            targetStatus="rejected",
        ),
    )

    deal = session.get(Deal, "deal-1")
    audit_logs = list(session.scalars(select(AdminAuditLog).order_by(AdminAuditLog.action)))
    event = session.scalar(select(DomainEvent))
    assert deal is not None
    assert event is not None
    assert reviewed.status == "resolved"
    assert deal.status == "rejected"
    assert deal.updated_at.replace(tzinfo=UTC) == NOW
    assert [audit_log.action for audit_log in audit_logs] == [
        "deal.status.changed",
        "report.resolved",
    ]
    assert audit_logs[0].target_type == "deal"
    assert audit_logs[0].target_id == "deal-1"
    assert audit_logs[0].previous_status == "active"
    assert audit_logs[0].new_status == "rejected"
    assert audit_logs[0].reason == "confirmed fraudulent listing"
    assert event.event_type == "deal.status.changed"
    assert event.aggregate_type == "deal"
    assert event.aggregate_id == "deal-1"
    assert event.payload_json["previousStatus"] == "active"
    assert event.payload_json["newStatus"] == "rejected"
    assert event.payload_json["actorUserId"] == "admin-1"


def test_admin_resolves_auction_report_with_target_status_and_records_status_event() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)
    report = use_cases.report_auction(
        actor=user(),
        auction_id="auction-1",
        request=ReportCreateRequest(reasonCode="fraud", description=None),
    )

    use_cases.review_report(
        actor=user(role="ADMIN"),
        report_id=report.id,
        request=ReportReviewRequest(
            status="resolved",
            resolutionNote="seller confirmed duplicate auction",
            targetStatus="blocked",
        ),
    )

    auction = session.get(Auction, "auction-1")
    event = session.scalar(select(DomainEvent))
    assert auction is not None
    assert event is not None
    assert auction.status == "blocked"
    assert event.event_type == "auction.status.changed"
    assert event.aggregate_type == "auction"
    assert event.aggregate_id == "auction-1"
    assert event.payload_json["previousStatus"] == "active"
    assert event.payload_json["newStatus"] == "blocked"


def test_admin_dismisses_report_without_target_status_does_not_change_offer_status() -> None:
    session = next(make_session())
    seed_data(session)
    use_cases = make_use_cases(session)
    report = use_cases.report_auction(
        actor=user(),
        auction_id="auction-1",
        request=ReportCreateRequest(reasonCode="broken_link", description=None),
    )

    reviewed = use_cases.review_report(
        actor=user(role="ADMIN"),
        report_id=report.id,
        request=ReportReviewRequest(status="dismissed", resolutionNote="not reproducible"),
    )

    auction = session.get(Auction, "auction-1")
    events = list(session.scalars(select(DomainEvent)))
    assert auction is not None
    assert reviewed.status == "dismissed"
    assert auction.status == "active"
    assert events == []
