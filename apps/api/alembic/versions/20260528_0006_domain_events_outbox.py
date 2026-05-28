"""domain events outbox

Revision ID: 20260528_0006
Revises: 20260528_0005
Create Date: 2026-05-28 21:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260528_0006"
down_revision: str | None = "20260528_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", sa.String(length=36), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_domain_events")),
    )
    op.create_index(
        "ix_domain_events_published_at_created_at",
        "domain_events",
        ["published_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_domain_events_event_type",
        "domain_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_domain_events_aggregate",
        "domain_events",
        ["aggregate_type", "aggregate_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_domain_events_aggregate", table_name="domain_events")
    op.drop_index("ix_domain_events_event_type", table_name="domain_events")
    op.drop_index("ix_domain_events_published_at_created_at", table_name="domain_events")
    op.drop_table("domain_events")
