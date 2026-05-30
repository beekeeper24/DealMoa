from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    ForbiddenException,
    ReportNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.reports.models import OfferReport
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import ReportCreateRequest, ReportReviewRequest, ReportStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class ReportsUseCases:
    def __init__(
        self,
        *,
        repository: ReportsRepository,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.now = now or utc_now

    def report_deal(
        self,
        *,
        actor: AuthenticatedUser,
        deal_id: str,
        request: ReportCreateRequest,
    ) -> OfferReport:
        if self.repository.get_deal(deal_id) is None:
            raise DealNotFoundException(deal_id)
        return self._create_or_get_open_report(
            actor=actor,
            target_type="deal",
            target_id=deal_id,
            request=request,
        )

    def report_auction(
        self,
        *,
        actor: AuthenticatedUser,
        auction_id: str,
        request: ReportCreateRequest,
    ) -> OfferReport:
        if self.repository.get_auction(auction_id) is None:
            raise AuctionNotFoundException(auction_id)
        return self._create_or_get_open_report(
            actor=actor,
            target_type="auction",
            target_id=auction_id,
            request=request,
        )

    def list_reports(
        self,
        *,
        actor: AuthenticatedUser,
        status: ReportStatus,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[OfferReport]:
        self._ensure_admin(actor)
        return self.repository.list_reports(status=status, limit=limit, cursor=cursor)

    def review_report(
        self,
        *,
        actor: AuthenticatedUser,
        report_id: str,
        request: ReportReviewRequest,
    ) -> OfferReport:
        self._ensure_admin(actor)
        report = self.repository.get_report(report_id)
        if report is None:
            raise ReportNotFoundException(report_id)

        previous_status = report.status
        now = self.now()
        report.status = request.status
        report.reviewed_by_user_id = actor.id
        report.resolution_note = request.resolution_note
        report.resolved_at = now
        report.updated_at = now
        self.repository.create_audit_log(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=f"report.{request.status}",
                target_type="report",
                target_id=report.id,
                previous_status=previous_status,
                new_status=request.status,
                reason=request.resolution_note,
                created_at=now,
                updated_at=now,
            )
        )
        return report

    def _create_or_get_open_report(
        self,
        *,
        actor: AuthenticatedUser,
        target_type: str,
        target_id: str,
        request: ReportCreateRequest,
    ) -> OfferReport:
        existing = self.repository.get_open_report(
            user_id=actor.id,
            target_type=target_type,
            target_id=target_id,
        )
        if existing is not None:
            return existing

        now = self.now()
        return self.repository.create_report(
            OfferReport(
                user_id=actor.id,
                target_type=target_type,
                target_id=target_id,
                reason_code=request.reason_code,
                description=request.description,
                status="open",
                created_at=now,
                updated_at=now,
            )
        )

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()
