"""notification target dedupe

Revision ID: 20260528_0005
Revises: 20260528_0004
Create Date: 2026-05-28 21:40:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260528_0005"
down_revision: str | None = "20260528_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_notifications_user_type_target",
        "notifications",
        ["user_id", "type", "target_type", "target_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_notifications_user_type_target", table_name="notifications")
