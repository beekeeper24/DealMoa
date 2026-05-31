from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.admin.models import AdminAuditLog
from app.modules.submissions.models import Submission

SubmissionT = TypeVar("SubmissionT", bound=Submission)


class SubmissionsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_submission(self, submission: Submission) -> Submission:
        self.session.add(submission)
        self.session.flush()
        return submission

    def get_submission(self, submission_id: str) -> Submission | None:
        return self.session.get(Submission, submission_id)

    def get_submission_by_source_url(self, source_url: str) -> Submission | None:
        statement = select(Submission).where(Submission.source_url == source_url)
        return self.session.scalar(statement)

    def list_user_submissions(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Submission]:
        statement = (
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
        )
        if cursor is not None:
            cursor_submission = self.get_submission(cursor)
            if cursor_submission is None or cursor_submission.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, Submission, cursor_submission)
        return self._page(statement, limit)

    def list_admin_submissions(
        self,
        *,
        status: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Submission]:
        statement = (
            select(Submission)
            .where(Submission.status == status)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
        )
        if cursor is not None:
            cursor_submission = self.get_submission(cursor)
            if cursor_submission is None or cursor_submission.status != status:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, Submission, cursor_submission)
        return self._page(statement, limit)

    def create_audit_log(self, audit_log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(audit_log)
        self.session.flush()
        return audit_log

    def _page(self, statement: Select[tuple[SubmissionT]], limit: int) -> CursorPage[SubmissionT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[SubmissionT]],
        model: type[SubmissionT],
        cursor_item: SubmissionT,
    ) -> Select[tuple[SubmissionT]]:
        return statement.where(
            or_(
                model.created_at < cursor_item.created_at,
                and_(model.created_at == cursor_item.created_at, model.id < cursor_item.id),
            )
        )
