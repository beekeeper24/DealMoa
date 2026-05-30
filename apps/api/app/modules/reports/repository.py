from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.products.models import Auction, Deal
from app.modules.reports.models import OfferReport

ReportT = TypeVar("ReportT", bound=OfferReport)


class ReportsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_deal(self, deal_id: str) -> Deal | None:
        return self.session.get(Deal, deal_id)

    def get_auction(self, auction_id: str) -> Auction | None:
        return self.session.get(Auction, auction_id)

    def get_report(self, report_id: str) -> OfferReport | None:
        return self.session.get(OfferReport, report_id)

    def get_open_report(
        self,
        *,
        user_id: str,
        target_type: str,
        target_id: str,
    ) -> OfferReport | None:
        statement = select(OfferReport).where(
            OfferReport.user_id == user_id,
            OfferReport.target_type == target_type,
            OfferReport.target_id == target_id,
            OfferReport.status == "open",
        )
        return self.session.scalar(statement)

    def create_report(self, report: OfferReport) -> OfferReport:
        self.session.add(report)
        self.session.flush()
        return report

    def create_audit_log(self, audit_log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(audit_log)
        self.session.flush()
        return audit_log

    def list_reports(
        self,
        *,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[OfferReport]:
        statement = (
            select(OfferReport)
            .where(OfferReport.status == status)
            .order_by(OfferReport.created_at.desc(), OfferReport.id.desc())
        )
        if cursor is not None:
            cursor_report = self.get_report(cursor)
            if cursor_report is None or cursor_report.status != status:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, OfferReport, cursor_report)
        return self._page(statement, limit)

    def _page(self, statement: Select[tuple[ReportT]], limit: int) -> CursorPage[ReportT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[ReportT]],
        model: type[ReportT],
        cursor_item: ReportT,
    ) -> Select[tuple[ReportT]]:
        return statement.where(
            or_(
                model.created_at < cursor_item.created_at,
                and_(model.created_at == cursor_item.created_at, model.id < cursor_item.id),
            )
        )
