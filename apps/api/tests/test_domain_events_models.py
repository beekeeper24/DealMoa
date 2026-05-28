from typing import cast

from app.db.base import Base
from app.modules.events.models import DomainEvent
from sqlalchemy import Index, Table


def test_domain_events_table_is_registered() -> None:
    assert "domain_events" in Base.metadata.tables
    assert DomainEvent.__tablename__ == "domain_events"


def test_domain_event_columns_support_transactional_outbox() -> None:
    table = cast(Table, DomainEvent.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "payload_json",
        "published_at",
        "created_at",
        "updated_at",
    }
    assert table.c.event_type.nullable is False
    assert table.c.aggregate_type.nullable is False
    assert table.c.aggregate_id.nullable is False
    assert table.c.payload_json.nullable is False
    assert table.c.published_at.nullable is True


def test_domain_event_has_publisher_indexes() -> None:
    table = cast(Table, DomainEvent.__table__)
    indexes = {index.name for index in table.indexes if isinstance(index, Index)}

    assert {
        "ix_domain_events_published_at_created_at",
        "ix_domain_events_event_type",
        "ix_domain_events_aggregate",
    } <= indexes
