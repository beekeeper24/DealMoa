from typing import cast

from app.db.base import Base
from app.modules.admin.models import AdminAuditLog
from sqlalchemy import ForeignKeyConstraint, Index, Table


def test_admin_audit_log_table_is_registered() -> None:
    assert "admin_audit_logs" in Base.metadata.tables
    assert AdminAuditLog.__tablename__ == "admin_audit_logs"


def test_admin_audit_log_records_actor_action_target_and_status_change() -> None:
    table = cast(Table, AdminAuditLog.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "actor_user_id",
        "action",
        "target_type",
        "target_id",
        "previous_status",
        "new_status",
        "reason",
        "created_at",
        "updated_at",
    }
    assert table.c.actor_user_id.nullable is False
    assert table.c.action.nullable is False
    assert table.c.target_type.nullable is False
    assert table.c.target_id.nullable is False
    assert table.c.new_status.nullable is False
    assert table.c.reason.nullable

    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 1
    assert foreign_keys[0].referred_table.name == "users"


def test_admin_audit_log_indexes_support_actor_and_target_lookup() -> None:
    indexes = {
        index.name
        for index in cast(Table, AdminAuditLog.__table__).indexes
        if isinstance(index, Index)
    }

    assert {
        "ix_admin_audit_logs_actor_user_id_created_at",
        "ix_admin_audit_logs_target",
        "ix_admin_audit_logs_action_created_at",
    } <= indexes
