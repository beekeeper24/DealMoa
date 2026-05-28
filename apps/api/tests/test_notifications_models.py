from typing import cast

from app.db.base import Base
from app.modules.notifications.models import Notification, NotificationType
from sqlalchemy import ForeignKeyConstraint, Index, Table, inspect


def test_notification_table_is_registered() -> None:
    assert "notifications" in Base.metadata.tables
    assert Notification.__tablename__ == "notifications"


def test_notification_type_constants_are_stable_api_values() -> None:
    assert NotificationType.NEW_DEAL == "new_deal"
    assert NotificationType.NEW_AUCTION == "new_auction"
    assert NotificationType.AUCTION_ENDING_SOON == "auction_ending_soon"


def test_notification_columns_support_user_scoped_inbox() -> None:
    table = cast(Table, Notification.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "type",
        "title",
        "body",
        "target_type",
        "target_id",
        "metadata_json",
        "read_at",
        "created_at",
        "updated_at",
    }
    assert table.c.user_id.nullable is False
    assert table.c.type.nullable is False
    assert table.c.title.nullable is False
    assert table.c.read_at.nullable is True


def test_notification_references_user_and_has_inbox_indexes() -> None:
    table = cast(Table, Notification.__table__)
    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    indexes = {index.name for index in table.indexes if isinstance(index, Index)}

    assert len(foreign_keys) == 1
    assert foreign_keys[0].referred_table.name == "users"
    assert {
        "ix_notifications_user_id_created_at",
        "ix_notifications_user_id_read_at",
        "uq_notifications_user_type_target",
    } <= indexes


def test_notification_relationship_to_user() -> None:
    assert inspect(Notification).relationships.user.mapper.class_.__name__ == "User"
