"""auction bids baseline

Revision ID: 20260529_0007
Revises: 20260528_0006
Create Date: 2026-05-29 01:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0007"
down_revision: str | None = "20260528_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auction_bids",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("auction_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["auction_id"],
            ["auctions.id"],
            name=op.f("fk_auction_bids_auction_id_auctions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auction_bids_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auction_bids")),
    )
    op.create_index(
        "ix_auction_bids_auction_id",
        "auction_bids",
        ["auction_id"],
        unique=False,
    )
    op.create_index(
        "ix_auction_bids_user_id",
        "auction_bids",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auction_bids_user_id", table_name="auction_bids")
    op.drop_index("ix_auction_bids_auction_id", table_name="auction_bids")
    op.drop_table("auction_bids")
