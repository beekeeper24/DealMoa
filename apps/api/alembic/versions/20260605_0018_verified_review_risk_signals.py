"""verified review risk signals

Revision ID: 20260605_0018
Revises: 20260604_0017
Create Date: 2026-06-05 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260605_0018"
down_revision: str | None = "20260604_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "verified_reviews",
        sa.Column(
            "moderation_risk_score",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "verified_reviews",
        sa.Column(
            "moderation_risk_level",
            sa.String(length=20),
            nullable=False,
            server_default="low",
        ),
    )
    op.add_column(
        "verified_reviews",
        sa.Column(
            "moderation_risk_reasons_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.create_index(
        "ix_verified_reviews_status_risk_created_at",
        "verified_reviews",
        ["status", "moderation_risk_score", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verified_reviews_status_risk_created_at",
        table_name="verified_reviews",
    )
    op.drop_column("verified_reviews", "moderation_risk_reasons_json")
    op.drop_column("verified_reviews", "moderation_risk_level")
    op.drop_column("verified_reviews", "moderation_risk_score")
