"""crawler run log failures

Revision ID: 20260604_0015
Revises: 20260603_0014
Create Date: 2026-06-04 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0015"
down_revision: str | None = "20260603_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("crawler_run_logs", sa.Column("error_type", sa.String(length=120), nullable=True))
    op.add_column(
        "crawler_run_logs",
        sa.Column("error_message", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crawler_run_logs", "error_message")
    op.drop_column("crawler_run_logs", "error_type")
