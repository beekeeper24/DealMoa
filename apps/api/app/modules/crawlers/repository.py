from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.crawlers.models import CrawlerRunLog

CrawlerRunLogT = TypeVar("CrawlerRunLogT", bound=CrawlerRunLog)


class CrawlerRunLogsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run_log: CrawlerRunLog) -> CrawlerRunLog:
        self.session.add(run_log)
        self.session.flush()
        return run_log

    def get(self, run_log_id: str) -> CrawlerRunLog | None:
        return self.session.get(CrawlerRunLog, run_log_id)

    def list_run_logs(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[CrawlerRunLog]:
        statement = select(CrawlerRunLog).order_by(
            CrawlerRunLog.created_at.desc(),
            CrawlerRunLog.id.desc(),
        )
        if cursor is not None:
            cursor_run_log = self.get(cursor)
            if cursor_run_log is None:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, CrawlerRunLog, cursor_run_log)
        return self._page(statement, limit)

    def _page(
        self,
        statement: Select[tuple[CrawlerRunLogT]],
        limit: int,
    ) -> CursorPage[CrawlerRunLogT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[CrawlerRunLogT]],
        model: type[CrawlerRunLogT],
        cursor_item: CrawlerRunLogT,
    ) -> Select[tuple[CrawlerRunLogT]]:
        return statement.where(
            or_(
                model.created_at < cursor_item.created_at,
                and_(model.created_at == cursor_item.created_at, model.id < cursor_item.id),
            )
        )
