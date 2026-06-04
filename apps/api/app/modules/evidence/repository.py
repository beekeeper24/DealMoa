from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.evidence.models import PriceHistorySnapshot, VerifiedReview

EvidenceT = TypeVar("EvidenceT", PriceHistorySnapshot, VerifiedReview)


class EvidenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_price_snapshot(self, snapshot: PriceHistorySnapshot) -> PriceHistorySnapshot:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def list_price_history(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[PriceHistorySnapshot]:
        statement = (
            select(PriceHistorySnapshot)
            .where(PriceHistorySnapshot.product_id == product_id)
            .order_by(PriceHistorySnapshot.observed_at.desc(), PriceHistorySnapshot.id.desc())
        )
        if cursor is not None:
            cursor_item = self.session.get(PriceHistorySnapshot, cursor)
            if cursor_item is None or cursor_item.product_id != product_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_price_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def create_verified_review(self, review: VerifiedReview) -> VerifiedReview:
        self.session.add(review)
        self.session.flush()
        return review

    def get_verified_review(self, review_id: str) -> VerifiedReview | None:
        return self.session.get(VerifiedReview, review_id)

    def create_audit_log(self, audit_log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(audit_log)
        self.session.flush()
        return audit_log

    def list_product_verified_reviews(
        self,
        *,
        product_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        statement = (
            select(VerifiedReview)
            .where(VerifiedReview.product_id == product_id, VerifiedReview.status == "approved")
            .order_by(VerifiedReview.created_at.desc(), VerifiedReview.id.desc())
        )
        if cursor is not None:
            cursor_item = self.session.get(VerifiedReview, cursor)
            if (
                cursor_item is None
                or cursor_item.product_id != product_id
                or cursor_item.status != "approved"
            ):
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_review_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def list_admin_verified_reviews(
        self,
        *,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        statement = (
            select(VerifiedReview)
            .where(VerifiedReview.status == status)
            .order_by(
                VerifiedReview.moderation_risk_score.desc(),
                VerifiedReview.created_at.desc(),
                VerifiedReview.id.desc(),
            )
        )
        if cursor is not None:
            cursor_item = self.session.get(VerifiedReview, cursor)
            if cursor_item is None or cursor_item.status != status:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_admin_review_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def has_verified_review_with_proof_reference(self, proof_reference: str) -> bool:
        return self.session.scalar(
            select(VerifiedReview.id)
            .where(VerifiedReview.proof_reference == proof_reference)
            .limit(1)
        ) is not None

    def has_user_verified_review_for_product(self, *, product_id: str, user_id: str) -> bool:
        return self.session.scalar(
            select(VerifiedReview.id)
            .where(
                VerifiedReview.product_id == product_id,
                VerifiedReview.user_id == user_id,
            )
            .limit(1)
        ) is not None

    def list_user_verified_reviews(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[VerifiedReview]:
        statement = (
            select(VerifiedReview)
            .where(VerifiedReview.user_id == user_id)
            .order_by(VerifiedReview.created_at.desc(), VerifiedReview.id.desc())
        )
        if cursor is not None:
            cursor_item = self.session.get(VerifiedReview, cursor)
            if cursor_item is None or cursor_item.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_review_cursor(statement, cursor_item)
        return self._page(statement, limit)

    def _page(
        self,
        statement: Select[tuple[EvidenceT]],
        limit: int,
    ) -> CursorPage[EvidenceT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_price_cursor(
        self,
        statement: Select[tuple[PriceHistorySnapshot]],
        cursor_item: PriceHistorySnapshot,
    ) -> Select[tuple[PriceHistorySnapshot]]:
        return statement.where(
            or_(
                PriceHistorySnapshot.observed_at < cursor_item.observed_at,
                and_(
                    PriceHistorySnapshot.observed_at == cursor_item.observed_at,
                    PriceHistorySnapshot.id < cursor_item.id,
                ),
            )
        )

    def _apply_review_cursor(
        self,
        statement: Select[tuple[VerifiedReview]],
        cursor_item: VerifiedReview,
    ) -> Select[tuple[VerifiedReview]]:
        return statement.where(
            or_(
                VerifiedReview.created_at < cursor_item.created_at,
                and_(
                    VerifiedReview.created_at == cursor_item.created_at,
                    VerifiedReview.id < cursor_item.id,
                ),
            )
        )

    def _apply_admin_review_cursor(
        self,
        statement: Select[tuple[VerifiedReview]],
        cursor_item: VerifiedReview,
    ) -> Select[tuple[VerifiedReview]]:
        return statement.where(
            or_(
                VerifiedReview.moderation_risk_score < cursor_item.moderation_risk_score,
                and_(
                    VerifiedReview.moderation_risk_score == cursor_item.moderation_risk_score,
                    VerifiedReview.created_at < cursor_item.created_at,
                ),
                and_(
                    VerifiedReview.moderation_risk_score == cursor_item.moderation_risk_score,
                    VerifiedReview.created_at == cursor_item.created_at,
                    VerifiedReview.id < cursor_item.id,
                ),
            )
        )
