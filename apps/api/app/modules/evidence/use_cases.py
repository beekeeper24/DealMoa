from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import (
    ForbiddenException,
    ProductNotFoundException,
    VerifiedReviewAlreadyReviewedException,
    VerifiedReviewNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.ai_review.provider import AiReviewProvider, AIReviewResult, MockAiReviewProvider
from app.modules.ai_review.rate_limits import AIReviewRateLimiter
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.evidence.models import PriceHistorySnapshot, VerifiedReview
from app.modules.evidence.repository import EvidenceRepository
from app.modules.evidence.schemas import (
    VerifiedReviewCreateRequest,
    VerifiedReviewReviewRequest,
)
from app.modules.products.repository import ProductRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


class EvidenceUseCases:
    def __init__(
        self,
        *,
        evidence_repository: EvidenceRepository,
        product_repository: ProductRepository,
        domain_events: DomainEventsUseCases | None = None,
        ai_review_provider: AiReviewProvider | None = None,
        ai_review_rate_limiter: AIReviewRateLimiter | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.evidence_repository = evidence_repository
        self.product_repository = product_repository
        self.domain_events = domain_events
        self.ai_review_provider = ai_review_provider or MockAiReviewProvider()
        self.ai_review_rate_limiter = ai_review_rate_limiter
        self.now = now or utc_now

    def record_price_snapshot(
        self,
        *,
        product_id: str,
        source_type: str,
        source_id: str,
        price: int,
        currency: str,
        observed_at: datetime | None = None,
    ) -> PriceHistorySnapshot:
        now = self.now()
        return self.evidence_repository.create_price_snapshot(
            PriceHistorySnapshot(
                product_id=product_id,
                source_type=source_type,
                source_id=source_id,
                price=price,
                currency=currency,
                observed_at=observed_at or now,
                created_at=now,
                updated_at=now,
            )
        )

    def list_price_history(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[PriceHistorySnapshot]:
        self._ensure_product_exists(product_id)
        return self.evidence_repository.list_price_history(
            product_id=product_id,
            limit=limit,
            cursor=cursor,
        )

    def create_verified_review(
        self,
        *,
        actor: AuthenticatedUser,
        product_id: str,
        request: VerifiedReviewCreateRequest,
    ) -> VerifiedReview:
        self._ensure_product_exists(product_id)
        now = self.now()
        if self.ai_review_rate_limiter is not None:
            self.ai_review_rate_limiter.check_and_record(
                user_id=actor.id,
                target_type="verified_review",
                now=now,
            )
        ai_review = self.ai_review_provider.review_verified_review(request)
        return self.evidence_repository.create_verified_review(
            VerifiedReview(
                product_id=product_id,
                user_id=actor.id,
                rating=request.rating,
                title=request.title,
                body=request.body,
                proof_type=request.proof_type,
                proof_reference=request.proof_reference,
                status="pending_review",
                ai_decision=ai_review.decision,
                ai_reason=ai_review.reason,
                ai_reviewed_at=now,
                created_at=now,
                updated_at=now,
            )
        )

    def list_product_verified_reviews(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        self._ensure_product_exists(product_id)
        return self.evidence_repository.list_product_verified_reviews(
            product_id=product_id,
            limit=limit,
            cursor=cursor,
        )

    def list_admin_verified_reviews(
        self,
        *,
        actor: AuthenticatedUser,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        self._ensure_admin(actor)
        return self.evidence_repository.list_admin_verified_reviews(
            status=status,
            limit=limit,
            cursor=cursor,
        )

    def list_my_verified_reviews(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        return self.evidence_repository.list_user_verified_reviews(
            user_id=actor.id,
            limit=limit,
            cursor=cursor,
        )

    def review_verified_review(
        self,
        *,
        actor: AuthenticatedUser,
        review_id: str,
        request: VerifiedReviewReviewRequest,
    ) -> VerifiedReview:
        self._ensure_admin(actor)
        review = self.evidence_repository.get_verified_review(review_id)
        if review is None:
            raise VerifiedReviewNotFoundException(review_id)
        if review.status != "pending_review":
            raise VerifiedReviewAlreadyReviewedException(review.id, review.status)

        now = self.now()
        previous_status = review.status
        if request.action == "approve":
            review.status = "approved"
            action = "verified_review.approved"
        else:
            review.status = "rejected"
            action = "verified_review.rejected"

        review.reviewed_by_user_id = actor.id
        review.resolution_note = request.resolution_note
        review.resolved_at = now
        review.updated_at = now
        self.evidence_repository.create_audit_log(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type="verified_review",
                target_id=review.id,
                previous_status=previous_status,
                new_status=review.status,
                reason=request.resolution_note,
                created_at=now,
                updated_at=now,
            )
        )
        if review.status == "approved" and self.domain_events is not None:
            self.domain_events.record_review_verified(review)
        return review

    def run_mock_ai_review(self, request: VerifiedReviewCreateRequest) -> AIReviewResult:
        return MockAiReviewProvider().review_verified_review(request)

    def _ensure_product_exists(self, product_id: str) -> None:
        if self.product_repository.get_product(product_id) is None:
            raise ProductNotFoundException(product_id)

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()
