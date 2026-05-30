"""auction views for view momentum

Revision ID: 20260531_0008
Revises: 20260529_0007
Create Date: 2026-05-31 01:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0008"
down_revision: str | None = "20260529_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auction_views",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("auction_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["auction_id"],
            ["auctions.id"],
            name=op.f("fk_auction_views_auction_id_auctions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auction_views")),
    )
    op.create_index(
        "ix_auction_views_auction_id_created_at",
        "auction_views",
        ["auction_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auction_views_auction_id_created_at", table_name="auction_views")
    op.drop_table("auction_views")
