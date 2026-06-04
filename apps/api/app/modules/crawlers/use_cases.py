from app.core.exceptions import ForbiddenException
from app.core.pagination import CursorPage
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.crawlers.models import CrawlerRunLog
from app.modules.crawlers.repository import CrawlerRunLogsRepository
from app.modules.crawlers.task_queue import CrawlerTaskName, CrawlerTaskQueue


class CrawlerRunLogsUseCases:
    def __init__(
        self,
        *,
        repository: CrawlerRunLogsRepository,
        task_queue: CrawlerTaskQueue | None = None,
    ) -> None:
        self.repository = repository
        self.task_queue = task_queue

    def list_run_logs(
        self,
        *,
        actor: AuthenticatedUser,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[CrawlerRunLog]:
        self._ensure_admin(actor)
        return self.repository.list_run_logs(limit=limit, cursor=cursor)

    def trigger_run(
        self,
        *,
        actor: AuthenticatedUser,
        task_name: CrawlerTaskName,
    ) -> str:
        self._ensure_admin(actor)
        if self.task_queue is None:
            raise RuntimeError("crawler task queue is not configured")
        return self.task_queue.enqueue(task_name)

    def _ensure_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role != "ADMIN":
            raise ForbiddenException()
