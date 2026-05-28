from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.notifications.repository import NotificationsRepository
from app.modules.notifications.schemas import (
    MarkAllNotificationsReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadNotificationCountResponse,
)
from app.modules.notifications.use_cases import NotificationsUseCases

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notifications_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> NotificationsUseCases:
    return NotificationsUseCases(repository=NotificationsRepository(session))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[NotificationsUseCases, Depends(get_notifications_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
    unread_only: bool = Query(default=False, alias="unreadOnly"),
) -> NotificationListResponse:
    page = use_cases.list_notifications(
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/unread-count", response_model=UnreadNotificationCountResponse)
def count_unread_notifications(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[NotificationsUseCases, Depends(get_notifications_use_cases)],
) -> UnreadNotificationCountResponse:
    return UnreadNotificationCountResponse(count=use_cases.count_unread(user_id=current_user.id))


@router.post("/read-all", response_model=MarkAllNotificationsReadResponse)
def mark_all_notifications_read(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[NotificationsUseCases, Depends(get_notifications_use_cases)],
) -> MarkAllNotificationsReadResponse:
    updated_count = use_cases.mark_all_read(user_id=current_user.id)
    return MarkAllNotificationsReadResponse(updatedCount=updated_count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[NotificationsUseCases, Depends(get_notifications_use_cases)],
) -> NotificationResponse:
    notification = use_cases.mark_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return NotificationResponse.model_validate(notification)
