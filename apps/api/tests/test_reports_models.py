from typing import cast

from app.db.base import Base
from app.modules.reports.models import OfferReport
from sqlalchemy import ForeignKeyConstraint, Index, Table


def test_offer_report_table_is_registered() -> None:
    assert "offer_reports" in Base.metadata.tables
    assert OfferReport.__tablename__ == "offer_reports"


def test_offer_report_records_user_target_reason_and_review_state() -> None:
    table = cast(Table, OfferReport.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "target_type",
        "target_id",
        "reason_code",
        "description",
        "status",
        "reviewed_by_user_id",
        "resolution_note",
        "resolved_at",
        "created_at",
        "updated_at",
    }
    assert table.c.user_id.nullable is False
    assert table.c.target_type.nullable is False
    assert table.c.target_id.nullable is False
    assert table.c.reason_code.nullable is False
    assert table.c.description.nullable
    assert table.c.status.nullable is False
    assert table.c.reviewed_by_user_id.nullable
    assert table.c.resolution_note.nullable
    assert table.c.resolved_at.nullable

    foreign_tables = {
        constraint.referred_table.name
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert foreign_tables == {"users"}


def test_offer_report_indexes_support_queue_and_user_target_lookup() -> None:
    indexes = {
        index.name
        for index in cast(Table, OfferReport.__table__).indexes
        if isinstance(index, Index)
    }

    assert {
        "ix_offer_reports_status_created_at",
        "ix_offer_reports_target",
        "ix_offer_reports_user_target_status",
    } <= indexes
