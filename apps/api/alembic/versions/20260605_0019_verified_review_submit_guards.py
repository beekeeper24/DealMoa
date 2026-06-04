"""verified review submit guards

Revision ID: 20260605_0019
Revises: 20260605_0018
Create Date: 2026-06-05 01:15:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260605_0019"
down_revision: str | None = "20260605_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("verified_reviews") as batch_op:
        batch_op.create_unique_constraint(
            "uq_verified_reviews_user_product",
            ["user_id", "product_id"],
        )
        batch_op.create_unique_constraint(
            "uq_verified_reviews_proof_reference",
            ["proof_reference"],
        )


def downgrade() -> None:
    with op.batch_alter_table("verified_reviews") as batch_op:
        batch_op.drop_constraint(
            "uq_verified_reviews_proof_reference",
            type_="unique",
        )
        batch_op.drop_constraint(
            "uq_verified_reviews_user_product",
            type_="unique",
        )
