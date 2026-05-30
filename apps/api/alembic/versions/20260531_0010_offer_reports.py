"""offer reports

Revision ID: 20260531_0010
Revises: 20260531_0009
Create Date: 2026-05-31 03:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0010"
down_revision: str | None = "20260531_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "offer_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_offer_reports_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f("fk_offer_reports_reviewed_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_offer_reports")),
    )
    op.create_index(
        "ix_offer_reports_status_created_at",
        "offer_reports",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_offer_reports_target",
        "offer_reports",
        ["target_type", "target_id"],
        unique=False,
    )
    op.create_index(
        "ix_offer_reports_user_target_status",
        "offer_reports",
        ["user_id", "target_type", "target_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_offer_reports_user_target_status", table_name="offer_reports")
    op.drop_index("ix_offer_reports_target", table_name="offer_reports")
    op.drop_index("ix_offer_reports_status_created_at", table_name="offer_reports")
    op.drop_table("offer_reports")
