"""price history and verified reviews

Revision ID: 20260601_0012
Revises: 20260531_0011
Create Date: 2026-06-01 00:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_0012"
down_revision: str | None = "20260531_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_history_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_price_history_snapshots_product_id_products"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_history_snapshots")),
    )
    op.create_index(
        "ix_price_history_product_observed_at",
        "price_history_snapshots",
        ["product_id", "observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_price_history_source",
        "price_history_snapshots",
        ["source_type", "source_id"],
        unique=False,
    )

    op.create_table(
        "verified_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("proof_type", sa.String(length=80), nullable=False),
        sa.Column("proof_reference", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ai_decision", sa.String(length=80), nullable=True),
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column("ai_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_verified_reviews_product_id_products"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f("fk_verified_reviews_reviewed_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_verified_reviews_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verified_reviews")),
    )
    op.create_index(
        "ix_verified_reviews_product_status_created_at",
        "verified_reviews",
        ["product_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_verified_reviews_status_created_at",
        "verified_reviews",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_verified_reviews_user_id_created_at",
        "verified_reviews",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_verified_reviews_user_id_created_at", table_name="verified_reviews")
    op.drop_index("ix_verified_reviews_status_created_at", table_name="verified_reviews")
    op.drop_index(
        "ix_verified_reviews_product_status_created_at",
        table_name="verified_reviews",
    )
    op.drop_table("verified_reviews")
    op.drop_index("ix_price_history_source", table_name="price_history_snapshots")
    op.drop_index(
        "ix_price_history_product_observed_at",
        table_name="price_history_snapshots",
    )
    op.drop_table("price_history_snapshots")
