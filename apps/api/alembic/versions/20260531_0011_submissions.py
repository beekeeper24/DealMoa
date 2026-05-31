"""submissions

Revision ID: 20260531_0011
Revises: 20260531_0010
Create Date: 2026-05-31 14:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0011"
down_revision: str | None = "20260531_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("offer_type", sa.String(length=30), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("seller", sa.String(length=120), nullable=True),
        sa.Column("original_price", sa.Integer(), nullable=True),
        sa.Column("sale_price", sa.Integer(), nullable=True),
        sa.Column("current_price", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ai_decision", sa.String(length=80), nullable=True),
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column("ai_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_product_id", sa.String(length=36), nullable=True),
        sa.Column("published_offer_type", sa.String(length=30), nullable=True),
        sa.Column("published_offer_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_submissions_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f("fk_submissions_reviewed_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
    )
    op.create_index(
        "ix_submissions_status_created_at",
        "submissions",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_user_id_created_at",
        "submissions",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_source_url",
        "submissions",
        ["source_url"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_submissions_source_url", table_name="submissions")
    op.drop_index("ix_submissions_user_id_created_at", table_name="submissions")
    op.drop_index("ix_submissions_status_created_at", table_name="submissions")
    op.drop_table("submissions")
