from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import ForbiddenException, ProductNotFoundException
from app.core.pagination import CursorPage
from app.db.base import Base
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.models import User
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.submissions.models import Submission
from app.modules.submissions.repository import SubmissionsRepository
from app.modules.submissions.schemas import SubmissionCreateRequest, SubmissionReviewRequest
from app.modules.submissions.use_cases import SubmissionsUseCases
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 31, 14, 0, tzinfo=UTC)


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


def seed_users(session: Session) -> None:
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
        ]
    )
    session.flush()


def actor(role: str = "USER") -> AuthenticatedUser:
    return AuthenticatedUser(
        id="admin-1" if role == "ADMIN" else "user-1",
        email="admin@example.com" if role == "ADMIN" else "user@example.com",
        nickname=role,
        role=role,
    )


def make_use_cases(session: Session) -> SubmissionsUseCases:
    return SubmissionsUseCases(
        submissions_repository=SubmissionsRepository(session),
        product_repository=ProductRepository(session),
        domain_events=DomainEventsUseCases(
            repository=DomainEventsRepository(session),
            now=lambda: NOW,
        ),
        now=lambda: NOW,
    )


def deal_request(
    source_url: str = "https://example.com/deals/galaxy-s26",
) -> SubmissionCreateRequest:
    return SubmissionCreateRequest(
        offerType="deal",
        sourceUrl=source_url,
        productName="Galaxy S26",
        brand="Samsung",
        modelName="SM-S260",
        category="smartphone",
        title="Galaxy S26 launch deal",
        seller="Example Store",
        originalPrice=1400000,
        salePrice=1090000,
        currentPrice=None,
        currency="KRW",
        description="Launch discount",
    )


def auction_request() -> SubmissionCreateRequest:
    return SubmissionCreateRequest(
        offerType="auction",
        sourceUrl="https://example.com/auctions/galaxy-s26",
        productName="Galaxy S26",
        brand="Samsung",
        modelName="SM-S260",
        category="smartphone",
        title="Galaxy S26 sealed auction",
        seller="Auction House",
        originalPrice=None,
        salePrice=None,
        currentPrice=720000,
        currency="KRW",
        description=None,
    )


def test_create_submission_runs_mock_ai_review_and_is_duplicate_url_idempotent() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)

    first = use_cases.create_submission(actor=actor(), request=deal_request())
    second = use_cases.create_submission(actor=actor(), request=deal_request())

    submissions = list(session.scalars(select(Submission)))
    assert first.submission.id == second.submission.id
    assert first.created is True
    assert second.created is False
    assert len(submissions) == 1
    assert first.submission.user_id == "user-1"
    assert first.submission.offer_type == "deal"
    assert first.submission.status == "pending_review"
    assert first.submission.ai_decision == "needs_admin_review"
    assert first.submission.ai_reason == "mock review passed: admin approval required"
    assert first.submission.ai_reviewed_at == NOW


def test_user_lists_own_submissions_only_with_cursor_pagination() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    first = use_cases.create_submission(actor=actor(), request=deal_request("https://example.com/1"))
    second = use_cases.create_submission(actor=actor(), request=deal_request("https://example.com/2"))

    first_page = use_cases.list_my_submissions(actor=actor(), limit=1, cursor=None)
    second_page = use_cases.list_my_submissions(
        actor=actor(),
        limit=1,
        cursor=first_page.next_cursor,
    )

    assert isinstance(first_page, CursorPage)
    assert first_page.next_cursor == first_page.items[0].id
    assert {first_page.items[0].id, second_page.items[0].id} == {
        first.submission.id,
        second.submission.id,
    }
    assert second_page.next_cursor is None


def test_admin_approval_publishes_deal_and_records_events_and_audit_log() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    reviewed = use_cases.review_submission(
        actor=actor(role="ADMIN"),
        submission_id=submission.submission.id,
        request=SubmissionReviewRequest(action="approve", resolutionNote="looks good"),
    )

    products = list(session.scalars(select(Product)))
    deals = list(session.scalars(select(Deal)))
    audit_logs = list(session.scalars(select(AdminAuditLog)))
    events = list(session.scalars(select(DomainEvent).order_by(DomainEvent.event_type)))
    assert reviewed.status == "approved"
    assert reviewed.reviewed_by_user_id == "admin-1"
    assert reviewed.resolution_note == "looks good"
    assert reviewed.published_product_id == products[0].id
    assert reviewed.published_offer_type == "deal"
    assert reviewed.published_offer_id == deals[0].id
    assert products[0].name == "Galaxy S26"
    assert deals[0].product_id == products[0].id
    assert deals[0].sale_price == 1090000
    assert deals[0].status == "active"
    assert audit_logs[0].action == "submission.approved"
    assert audit_logs[0].target_id == submission.submission.id
    assert {event.event_type for event in events} == {"deal.created", "product.updated"}


def test_admin_can_list_submission_product_matches_sorted_by_score() -> None:
    session = next(make_session())
    seed_users(session)
    session.add_all(
        [
            Product(
                id="product-1",
                name="Galaxy S26 Ultra",
                brand="Samsung",
                model_name="SM-S260",
                category="smartphone",
                specs=None,
                created_at=NOW,
                updated_at=NOW,
            ),
            Product(
                id="product-2",
                name="Galaxy Buds",
                brand="Samsung",
                model_name="Buds",
                category="audio",
                specs=None,
                created_at=NOW,
                updated_at=NOW,
            ),
        ]
    )
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    matches = use_cases.list_product_matches(
        actor=actor(role="ADMIN"),
        submission_id=submission.submission.id,
        limit=5,
    )

    assert [match.product.id for match in matches] == ["product-1", "product-2"]
    assert matches[0].score > matches[1].score
    assert "model" in matches[0].matched_reasons
    assert "brand" in matches[0].matched_reasons


def test_non_admin_cannot_list_submission_product_matches() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    with pytest.raises(ForbiddenException):
        use_cases.list_product_matches(
            actor=actor(),
            submission_id=submission.submission.id,
            limit=5,
        )


def test_admin_approval_can_attach_offer_to_existing_product() -> None:
    session = next(make_session())
    seed_users(session)
    existing_product = Product(
        id="product-1",
        name="Galaxy S26 Ultra",
        brand="Samsung",
        model_name="SM-S260",
        category="smartphone",
        specs=None,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(existing_product)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    reviewed = use_cases.review_submission(
        actor=actor(role="ADMIN"),
        submission_id=submission.submission.id,
        request=SubmissionReviewRequest(
            action="approve",
            targetProductId=existing_product.id,
            resolutionNote="기존 상품 연결",
        ),
    )

    products = list(session.scalars(select(Product)))
    deals = list(session.scalars(select(Deal)))
    events = list(session.scalars(select(DomainEvent).order_by(DomainEvent.event_type)))
    assert len(products) == 1
    assert reviewed.published_product_id == existing_product.id
    assert deals[0].product_id == existing_product.id
    assert {event.event_type for event in events} == {"deal.created", "product.updated"}


def test_admin_approval_rejects_missing_target_product() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    with pytest.raises(ProductNotFoundException):
        use_cases.review_submission(
            actor=actor(role="ADMIN"),
            submission_id=submission.submission.id,
            request=SubmissionReviewRequest(
                action="approve",
                targetProductId="missing-product",
                resolutionNote="기존 상품 연결",
            ),
        )


def test_admin_approval_publishes_auction() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=auction_request())

    reviewed = use_cases.review_submission(
        actor=actor(role="ADMIN"),
        submission_id=submission.submission.id,
        request=SubmissionReviewRequest(action="approve", resolutionNote=None),
    )

    auctions = list(session.scalars(select(Auction)))
    assert reviewed.status == "approved"
    assert reviewed.published_offer_type == "auction"
    assert reviewed.published_offer_id == auctions[0].id
    assert auctions[0].current_price == 720000
    assert auctions[0].status == "active"


def test_admin_rejection_does_not_publish_offer() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    reviewed = use_cases.review_submission(
        actor=actor(role="ADMIN"),
        submission_id=submission.submission.id,
        request=SubmissionReviewRequest(action="reject", resolutionNote="duplicate"),
    )

    assert reviewed.status == "rejected"
    assert reviewed.resolution_note == "duplicate"
    assert session.scalar(select(Product)) is None
    assert session.scalar(select(Deal)) is None


def test_non_admin_cannot_list_or_review_submissions() -> None:
    session = next(make_session())
    seed_users(session)
    use_cases = make_use_cases(session)
    submission = use_cases.create_submission(actor=actor(), request=deal_request())

    with pytest.raises(ForbiddenException):
        use_cases.list_admin_submissions(
            actor=actor(),
            status="pending_review",
            limit=20,
            cursor=None,
        )
    with pytest.raises(ForbiddenException):
        use_cases.review_submission(
            actor=actor(),
            submission_id=submission.submission.id,
            request=SubmissionReviewRequest(action="reject", resolutionNote=None),
        )
