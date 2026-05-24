"""product deal auction baseline

Revision ID: 20260525_0001
Revises:
Create Date: 2026-05-25 04:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260525_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("specs", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_model_name", "products", ["model_name"])

    op.create_table(
        "deals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("seller", sa.String(length=120), nullable=True),
        sa.Column("original_price", sa.Integer(), nullable=True),
        sa.Column("sale_price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_deals_product_id_products"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deals")),
    )
    op.create_index("ix_deals_product_id", "deals", ["product_id"])
    op.create_index("ix_deals_status", "deals", ["status"])

    op.create_table(
        "auctions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("seller", sa.String(length=120), nullable=True),
        sa.Column("current_price", sa.Integer(), nullable=False),
        sa.Column("bid_count", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_auctions_product_id_products"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auctions")),
    )
    op.create_index("ix_auctions_product_id", "auctions", ["product_id"])
    op.create_index("ix_auctions_status", "auctions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_auctions_status", table_name="auctions")
    op.drop_index("ix_auctions_product_id", table_name="auctions")
    op.drop_table("auctions")

    op.drop_index("ix_deals_status", table_name="deals")
    op.drop_index("ix_deals_product_id", table_name="deals")
    op.drop_table("deals")

    op.drop_index("ix_products_model_name", table_name="products")
    op.drop_index("ix_products_brand", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
