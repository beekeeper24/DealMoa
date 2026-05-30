"""admin audit logs

Revision ID: 20260531_0009
Revises: 20260531_0008
Create Date: 2026-05-31 02:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0009"
down_revision: str | None = "20260531_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_admin_audit_logs_actor_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_logs")),
    )
    op.create_index(
        "ix_admin_audit_logs_actor_user_id_created_at",
        "admin_audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_target",
        "admin_audit_logs",
        ["target_type", "target_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_action_created_at",
        "admin_audit_logs",
        ["action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_action_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_target", table_name="admin_audit_logs")
    op.drop_index(
        "ix_admin_audit_logs_actor_user_id_created_at",
        table_name="admin_audit_logs",
    )
    op.drop_table("admin_audit_logs")
