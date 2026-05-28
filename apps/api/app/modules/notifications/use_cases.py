from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.exceptions import NotificationNotFoundException
from app.core.pagination import CursorPage
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationsRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class NotificationCreate:
    user_id: str
    type: str
    title: str
    body: str
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict[str, object] | None = None


class NotificationsUseCases:
    def __init__(
        self,
        repository: NotificationsRepository,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository
        self.now = now

    def create_notification(self, request: NotificationCreate) -> Notification:
        now = self.now()
        return self.repository.create_notification(
            Notification(
                user_id=request.user_id,
                type=request.type,
                title=request.title,
                body=request.body,
                target_type=request.target_type,
                target_id=request.target_id,
                metadata_json=request.metadata or {},
                created_at=now,
                updated_at=now,
            )
        )

    def list_notifications(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
        unread_only: bool = False,
    ) -> CursorPage[Notification]:
        return self.repository.list_notifications(
            user_id=user_id,
            limit=limit,
            cursor=cursor,
            unread_only=unread_only,
        )

    def count_unread(self, *, user_id: str) -> int:
        return self.repository.count_unread(user_id=user_id)

    def mark_read(self, *, user_id: str, notification_id: str) -> Notification:
        notification = self.repository.get_notification(
            user_id=user_id,
            notification_id=notification_id,
        )
        if notification is None:
            raise NotificationNotFoundException(notification_id)
        if notification.read_at is None:
            now = self.now()
            notification.read_at = now
            notification.updated_at = now
        return notification

    def mark_all_read(self, *, user_id: str) -> int:
        return self.repository.mark_all_read(user_id=user_id, read_at=self.now())
