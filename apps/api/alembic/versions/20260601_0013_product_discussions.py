"""product discussion comments

Revision ID: 20260601_0013
Revises: 20260601_0012
Create Date: 2026-06-01 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_0013"
down_revision: str | None = "20260601_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_discussion_comments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("moderated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("moderation_note", sa.Text(), nullable=True),
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["moderated_by_user_id"],
            ["users.id"],
            name=op.f("fk_product_discussion_comments_moderated_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_discussion_comments_product_id_products"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_product_discussion_comments_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_discussion_comments")),
    )
    op.create_index(
        "ix_product_discussion_comments_product_status_created_at",
        "product_discussion_comments",
        ["product_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_product_discussion_comments_status_created_at",
        "product_discussion_comments",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_product_discussion_comments_user_id_created_at",
        "product_discussion_comments",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_discussion_comments_user_id_created_at",
        table_name="product_discussion_comments",
    )
    op.drop_index(
        "ix_product_discussion_comments_status_created_at",
        table_name="product_discussion_comments",
    )
    op.drop_index(
        "ix_product_discussion_comments_product_status_created_at",
        table_name="product_discussion_comments",
    )
    op.drop_table("product_discussion_comments")
