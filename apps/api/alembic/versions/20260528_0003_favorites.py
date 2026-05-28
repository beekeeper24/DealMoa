"""favorites baseline

Revision ID: 20260528_0003
Revises: 20260525_0002
Create Date: 2026-05-28 20:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260528_0003"
down_revision: str | None = "20260525_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_favorites_product_id_products"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_product_favorites_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_favorites")),
        sa.UniqueConstraint("user_id", "product_id", name="uq_product_favorites_user_product"),
    )
    op.create_index("ix_product_favorites_user_id", "product_favorites", ["user_id"])

    op.create_table(
        "deal_favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("deal_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["deals.id"],
            name=op.f("fk_deal_favorites_deal_id_deals"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_deal_favorites_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deal_favorites")),
        sa.UniqueConstraint("user_id", "deal_id", name="uq_deal_favorites_user_deal"),
    )
    op.create_index("ix_deal_favorites_user_id", "deal_favorites", ["user_id"])

    op.create_table(
        "auction_favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("auction_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["auction_id"],
            ["auctions.id"],
            name=op.f("fk_auction_favorites_auction_id_auctions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auction_favorites_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auction_favorites")),
        sa.UniqueConstraint("user_id", "auction_id", name="uq_auction_favorites_user_auction"),
    )
    op.create_index("ix_auction_favorites_user_id", "auction_favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_auction_favorites_user_id", table_name="auction_favorites")
    op.drop_table("auction_favorites")
    op.drop_index("ix_deal_favorites_user_id", table_name="deal_favorites")
    op.drop_table("deal_favorites")
    op.drop_index("ix_product_favorites_user_id", table_name="product_favorites")
    op.drop_table("product_favorites")
