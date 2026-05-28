from datetime import datetime

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.notifications.models import Notification


class NotificationsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_notification(self, notification: Notification) -> Notification:
        self.session.add(notification)
        self.session.flush()
        return notification

    def get_notification(self, *, user_id: str, notification_id: str) -> Notification | None:
        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.id == notification_id,
        )
        return self.session.scalar(statement)

    def get_notification_for_target(
        self,
        *,
        user_id: str,
        notification_type: str,
        target_type: str,
        target_id: str,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.type == notification_type,
            Notification.target_type == target_type,
            Notification.target_id == target_id,
        )
        return self.session.scalar(statement)

    def list_notifications(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
        unread_only: bool = False,
    ) -> CursorPage[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))
        if cursor is not None:
            cursor_notification = self.session.get(Notification, cursor)
            if cursor_notification is None or cursor_notification.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, cursor_notification)
        return self._page(statement, limit)

    def count_unread(self, *, user_id: str) -> int:
        statement = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        return self.session.scalar(statement) or 0

    def mark_all_read(self, *, user_id: str, read_at: datetime) -> int:
        notifications = list(
            self.session.scalars(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
            )
        )
        for notification in notifications:
            notification.read_at = read_at
            notification.updated_at = read_at
        self.session.flush()
        return len(notifications)

    def _page(
        self,
        statement: Select[tuple[Notification]],
        limit: int,
    ) -> CursorPage[Notification]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[Notification]],
        cursor_item: Notification,
    ) -> Select[tuple[Notification]]:
        return statement.where(
            or_(
                Notification.created_at < cursor_item.created_at,
                and_(
                    Notification.created_at == cursor_item.created_at,
                    Notification.id < cursor_item.id,
                ),
            )
        )
