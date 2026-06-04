import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.exceptions import (
    ForbiddenException,
    ProductNotFoundException,
    SubmissionAlreadyReviewedException,
    SubmissionNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.ai_review.provider import AiReviewProvider, AIReviewResult, MockAiReviewProvider
from app.modules.ai_review.rate_limits import AIReviewRateLimiter
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.models import Auction, Deal, Product
from app.modules.products.repository import ProductRepository
from app.modules.submissions.models import Submission
from app.modules.submissions.repository import SubmissionsRepository
from app.modules.submissions.schemas import SubmissionCreateRequest, SubmissionReviewRequest


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class SubmissionCreateResult:
    submission: Submission
    created: bool


@dataclass(frozen=True)
class ProductMatch:
    product: Product
    score: int
    matched_reasons: list[str]


class SubmissionsUseCases:
    def __init__(
        self,
        *,
        submissions_repository: SubmissionsRepository,
        product_repository: ProductRepository,
        domain_events: DomainEventsUseCases,
        ai_review_provider: AiReviewProvider | None = None,
        ai_review_rate_limiter: AIReviewRateLimiter | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.submissions_repository = submissions_repository
        self.product_repository = product_repository
        self.domain_events = domain_events
        self.ai_review_provider = ai_review_provider or MockAiReviewProvider()
        self.ai_review_rate_limiter = ai_review_rate_limiter
        self.now = now or utc_now

    def create_submission(
        self,
        *,
        actor: AuthenticatedUser,
        request: SubmissionCreateRequest,
    ) -> SubmissionCreateResult:
        existing = self.submissions_repository.get_submission_by_source_url(request.source_url)
        if existing is not None:
            return SubmissionCreateResult(submission=existing, created=False)

        now = self.now()
        if self.ai_review_rate_limiter is not None:
            self.ai_review_rate_limiter.check_and_record(
                user_id=actor.id,
                target_type="submission",
                now=now,
            )
        ai_review = self.ai_review_provider.review_submission(request)
        submission = self.submissions_repository.create_submission(
            Submission(
                user_id=actor.id,
                offer_type=request.offer_type,
                source_url=request.source_url,
                product_name=request.product_name,
                brand=request.brand,
                model_name=request.model_name,
                category=request.category,
                title=request.title,
                seller=request.seller,
                original_price=request.original_price,
                sale_price=request.sale_price,
                current_price=request.current_price,
                currency=request.currency,
                description=request.description,
                status="pending_review",
                ai_decision=ai_review.decision,
                ai_reason=ai_review.reason,
                ai_reviewed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        return SubmissionCreateResult(submission=submission, created=True)

    def list_my_submissions(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Submission]:
        return self.submissions_repository.list_user_submissions(
            user_id=actor.id,
            limit=limit,
            cursor=cursor,
        )

    def list_admin_submissions(
        self,
        *,
        actor: AuthenticatedUser,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Submission]:
        self._ensure_admin(actor)
        return self.submissions_repository.list_admin_submissions(
            status=status,
            limit=limit,
            cursor=cursor,
        )

    def list_product_matches(
        self,
        *,
        actor: AuthenticatedUser,
        submission_id: str,
        limit: int,
    ) -> list[ProductMatch]:
        self._ensure_admin(actor)
        submission = self.submissions_repository.get_submission(submission_id)
        if submission is None:
            raise SubmissionNotFoundException(submission_id)
        candidates = self.product_repository.list_products_for_matching(limit=100)
        matches = [
            match
            for product in candidates
            if (match := self._score_product_match(submission, product)).score > 0
        ]
        return sorted(matches, key=lambda match: (-match.score, match.product.name))[:limit]

    def review_submission(
        self,
        *,
        actor: AuthenticatedUser,
        submission_id: str,
        request: SubmissionReviewRequest,
    ) -> Submission:
        self._ensure_admin(actor)
        submission = self.submissions_repository.get_submission(submission_id)
        if submission is None:
            raise SubmissionNotFoundException(submission_id)
        if submission.status != "pending_review":
            raise SubmissionAlreadyReviewedException(submission.id, submission.status)

        now = self.now()
        previous_status = submission.status
        if request.action == "approve":
            self._approve_submission(submission, now, target_product_id=request.target_product_id)
            submission.status = "approved"
            action = "submission.approved"
        else:
            submission.status = "rejected"
            action = "submission.rejected"

        submission.reviewed_by_user_id = actor.id
        submission.resolution_note = request.resolution_note
        submission.resolved_at = now
        submission.updated_at = now
        self.submissions_repository.create_audit_log(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type="submission",
                target_id=submission.id,
                previous_status=previous_status,
                new_status=submission.status,
                reason=request.resolution_note,
                created_at=now,
                updated_at=now,
            )
        )
        return submission

    def run_mock_ai_review(self, request: SubmissionCreateRequest) -> AIReviewResult:
        return MockAiReviewProvider().review_submission(request)

    def _approve_submission(
        self,
        submission: Submission,
        now: datetime,
        *,
        target_product_id: str | None,
    ) -> None:
        if target_product_id is not None:
            product = self.product_repository.get_product(target_product_id)
            if product is None:
                raise ProductNotFoundException(target_product_id)
            product.updated_at = now
        else:
            product = self.product_repository.create_product(
                Product(
                    name=submission.product_name,
                    brand=submission.brand,
                    model_name=submission.model_name,
                    category=submission.category,
                    specs=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        self.domain_events.record_product_updated(product)
        submission.published_product_id = product.id

        if submission.offer_type == "deal":
            deal = self.product_repository.create_deal(
                Deal(
                    product_id=product.id,
                    title=submission.title,
                    source_url=submission.source_url,
                    seller=submission.seller,
                    original_price=submission.original_price,
                    sale_price=submission.sale_price or 0,
                    currency=submission.currency,
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
            self.domain_events.record_deal_created(deal)
            submission.published_offer_type = "deal"
            submission.published_offer_id = deal.id
            return

        auction = self.product_repository.create_auction(
            Auction(
                product_id=product.id,
                title=submission.title,
                source_url=submission.source_url,
                seller=submission.seller,
                current_price=submission.current_price or 0,
                bid_count=0,
                currency=submission.currency,
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        self.domain_events.record_auction_created(auction)
        submission.published_offer_type = "auction"
        submission.published_offer_id = auction.id

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()

    def _score_product_match(self, submission: Submission, product: Product) -> ProductMatch:
        score = 0
        reasons: list[str] = []
        submission_model = normalize_text(submission.model_name)
        product_model = normalize_text(product.model_name)
        if submission_model and product_model and submission_model == product_model:
            score += 55
            reasons.append("model")

        submission_brand = normalize_text(submission.brand)
        product_brand = normalize_text(product.brand)
        if submission_brand and product_brand and submission_brand == product_brand:
            score += 20
            reasons.append("brand")

        submission_category = normalize_text(submission.category)
        product_category = normalize_text(product.category)
        if submission_category and product_category and submission_category == product_category:
            score += 10
            reasons.append("category")

        shared_tokens = normalized_tokens(submission.product_name) & normalized_tokens(product.name)
        if shared_tokens:
            score += min(len(shared_tokens) * 10, 30)
            reasons.append("name")

        return ProductMatch(product=product, score=score, matched_reasons=reasons)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.casefold().strip().split())


def normalized_tokens(value: str | None) -> set[str]:
    normalized = normalize_text(value)
    if not normalized:
        return set()
    return {token for token in re.split(r"[^0-9a-z가-힣]+", normalized) if token}
