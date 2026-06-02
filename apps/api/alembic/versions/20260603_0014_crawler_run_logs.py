"""crawler run logs

Revision ID: 20260603_0014
Revises: 20260601_0013
Create Date: 2026-06-03 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0014"
down_revision: str | None = "20260601_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crawler_run_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("scanned_count", sa.Integer(), nullable=False),
        sa.Column("fetched_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("skip_reasons_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crawler_run_logs")),
    )
    op.create_index(
        "ix_crawler_run_logs_created_at",
        "crawler_run_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_crawler_run_logs_status_created_at",
        "crawler_run_logs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_crawler_run_logs_task_name_created_at",
        "crawler_run_logs",
        ["task_name", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_crawler_run_logs_task_name_created_at", table_name="crawler_run_logs")
    op.drop_index("ix_crawler_run_logs_status_created_at", table_name="crawler_run_logs")
    op.drop_index("ix_crawler_run_logs_created_at", table_name="crawler_run_logs")
    op.drop_table("crawler_run_logs")
