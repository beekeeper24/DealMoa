from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.crawlers.repository import CrawlerRunLogsRepository
from app.modules.crawlers.schemas import (
    CrawlerRunLogListResponse,
    CrawlerRunLogResponse,
    CrawlerRunTriggerRequest,
    CrawlerRunTriggerResponse,
)
from app.modules.crawlers.task_queue import CeleryCrawlerTaskQueue, CrawlerTaskQueue
from app.modules.crawlers.use_cases import CrawlerRunLogsUseCases

admin_router = APIRouter(prefix="/admin/crawler-runs", tags=["admin-crawler-runs"])


def get_crawler_task_queue() -> CrawlerTaskQueue:
    settings = get_settings()
    return CeleryCrawlerTaskQueue(broker_url=settings.celery_broker_url)


def get_crawler_run_logs_use_cases(
    session: Annotated[Session, Depends(get_session)],
    task_queue: Annotated[CrawlerTaskQueue, Depends(get_crawler_task_queue)],
) -> CrawlerRunLogsUseCases:
    return CrawlerRunLogsUseCases(
        repository=CrawlerRunLogsRepository(session),
        task_queue=task_queue,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@admin_router.get("", response_model=CrawlerRunLogListResponse)
def list_crawler_run_logs(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[CrawlerRunLogsUseCases, Depends(get_crawler_run_logs_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> CrawlerRunLogListResponse:
    page = use_cases.list_run_logs(actor=current_user, limit=limit, cursor=cursor)
    return CrawlerRunLogListResponse(
        items=[CrawlerRunLogResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.post("/trigger", response_model=CrawlerRunTriggerResponse)
def trigger_crawler_run(
    request: CrawlerRunTriggerRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[CrawlerRunLogsUseCases, Depends(get_crawler_run_logs_use_cases)],
) -> CrawlerRunTriggerResponse:
    celery_task_id = use_cases.trigger_run(actor=current_user, task_name=request.task_name)
    return CrawlerRunTriggerResponse(taskName=request.task_name, celeryTaskId=celery_task_id)
