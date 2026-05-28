from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from app.core.exceptions import NotificationNotFoundException
from app.db.base import Base
from app.modules.auth.models import User
from app.modules.notifications.models import Notification, NotificationType
from app.modules.notifications.repository import NotificationsRepository
from app.modules.notifications.use_cases import NotificationCreate, NotificationsUseCases
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def add_user(session: Session, user_id: str) -> User:
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        nickname=user_id,
        role="USER",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(user)
    return user


def make_use_cases(session: Session) -> NotificationsUseCases:
    return NotificationsUseCases(repository=NotificationsRepository(session), now=lambda: NOW)


def create_notification(
    use_cases: NotificationsUseCases,
    *,
    user_id: str = "user-1",
    notification_type: str = NotificationType.NEW_DEAL,
    title: str = "새 핫딜",
) -> Notification:
    return use_cases.create_notification(
        NotificationCreate(
            user_id=user_id,
            type=notification_type,
            title=title,
            body="관심 상품에 새 소식이 있습니다.",
            target_type="product",
            target_id="product-1",
            metadata={"source": "test"},
        )
    )


def test_create_and_list_notifications_are_user_scoped_and_paginated() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    use_cases = make_use_cases(session)
    first = create_notification(use_cases, user_id="user-1", title="첫 알림")
    second = create_notification(use_cases, user_id="user-1", title="둘째 알림")
    create_notification(use_cases, user_id="user-2", title="다른 사용자 알림")

    page = use_cases.list_notifications(user_id="user-1", limit=1, cursor=None)
    next_page = use_cases.list_notifications(
        user_id="user-1",
        limit=1,
        cursor=page.next_cursor,
    )

    assert [item.user_id for item in page.items + next_page.items] == ["user-1", "user-1"]
    assert {item.id for item in page.items + next_page.items} == {first.id, second.id}
    assert page.next_cursor is not None


def test_unread_filter_count_read_one_and_read_all() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    use_cases = make_use_cases(session)
    first = create_notification(use_cases)
    second = create_notification(use_cases, notification_type=NotificationType.NEW_AUCTION)
    session.flush()
    first.read_at = NOW - timedelta(minutes=1)

    unread_page = use_cases.list_notifications(
        user_id="user-1",
        limit=20,
        cursor=None,
        unread_only=True,
    )
    assert [item.id for item in unread_page.items] == [second.id]
    assert use_cases.count_unread(user_id="user-1") == 1

    read_second = use_cases.mark_read(user_id="user-1", notification_id=second.id)
    assert read_second.read_at == NOW
    assert use_cases.count_unread(user_id="user-1") == 0

    third = create_notification(use_cases, notification_type=NotificationType.AUCTION_ENDING_SOON)
    fourth = create_notification(use_cases, title="넷째 알림")
    assert use_cases.mark_all_read(user_id="user-1") == 2
    assert {third.read_at, fourth.read_at} == {NOW}


def test_mark_read_rejects_missing_or_other_user_notification() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    use_cases = make_use_cases(session)
    other_user_notification = create_notification(use_cases, user_id="user-2")

    with pytest.raises(NotificationNotFoundException) as missing:
        use_cases.mark_read(user_id="user-1", notification_id="missing-notification")

    with pytest.raises(NotificationNotFoundException) as cross_user:
        use_cases.mark_read(user_id="user-1", notification_id=other_user_notification.id)

    assert missing.value.error_code.code == "NOTIFICATION_NOT_FOUND"
    assert cross_user.value.details == {"notificationId": other_user_notification.id}


def test_notification_metadata_is_stored_as_json() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    use_cases = make_use_cases(session)

    notification = create_notification(use_cases)
    session.commit()

    stored = session.scalars(select(Notification)).one()
    assert stored.id == notification.id
    assert stored.metadata_json == {"source": "test"}
