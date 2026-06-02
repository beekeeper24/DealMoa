from app.core.exceptions import ForbiddenException
from app.core.pagination import CursorPage
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.crawlers.models import CrawlerRunLog
from app.modules.crawlers.repository import CrawlerRunLogsRepository


class CrawlerRunLogsUseCases:
    def __init__(self, *, repository: CrawlerRunLogsRepository) -> None:
        self.repository = repository

    def list_run_logs(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[CrawlerRunLog]:
        self._ensure_admin(actor)
        return self.repository.list_run_logs(limit=limit, cursor=cursor)

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()
