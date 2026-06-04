"""ai review usage events

Revision ID: 20260604_0017
Revises: 20260604_0016
Create Date: 2026-06-04 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0017"
down_revision: str | None = "20260604_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_review_usage_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ai_review_usage_events_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_review_usage_events")),
    )
    op.create_index(
        "ix_ai_review_usage_events_user_id_created_at",
        "ai_review_usage_events",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ai_review_usage_events_user_target_created_at",
        "ai_review_usage_events",
        ["user_id", "target_type", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ai_review_usage_events_user_target_created_at",
        table_name="ai_review_usage_events",
    )
    op.drop_index(
        "ix_ai_review_usage_events_user_id_created_at",
        table_name="ai_review_usage_events",
    )
    op.drop_table("ai_review_usage_events")
