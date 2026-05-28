import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from app.db.base import Base
from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from consumer_app.outbox_publisher import EventProducer, OutboxPublisher
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, 15, 0, tzinfo=UTC)


class FakeProducer(EventProducer):
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, object]]] = []

    async def publish(self, *, topic: str, message: dict[str, object]) -> None:
        self.messages.append((topic, message))


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def add_event(
    session: Session,
    *,
    event_id: str,
    event_type: str,
    published_at: datetime | None = None,
) -> None:
    session.add(
        DomainEvent(
            id=event_id,
            event_type=event_type,
            aggregate_type="deal",
            aggregate_id="deal-1",
            payload_json={"dealId": "deal-1"},
            published_at=published_at,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def test_publish_batch_sends_unpublished_events_and_marks_them_published() -> None:
    session = next(make_session())
    add_event(session, event_id="event-1", event_type="deal.created")
    add_event(session, event_id="event-2", event_type="auction.created")
    producer = FakeProducer()
    publisher = OutboxPublisher(
        repository=DomainEventsRepository(session),
        producer=producer,
        topic="dealmoa.domain-events",
        now=lambda: NOW + timedelta(minutes=1),
    )

    published_count = asyncio.run(publisher.publish_batch(limit=10))

    events = list(session.scalars(select(DomainEvent).order_by(DomainEvent.id)))
    assert published_count == 2
    assert [topic for topic, _message in producer.messages] == [
        "dealmoa.domain-events",
        "dealmoa.domain-events",
    ]
    assert [message["eventId"] for _topic, message in producer.messages] == ["event-1", "event-2"]
    assert producer.messages[0][1]["eventType"] == "deal.created"
    assert {event.published_at for event in events} == {
        (NOW + timedelta(minutes=1)).replace(tzinfo=None)
    }


def test_publish_batch_skips_already_published_events() -> None:
    session = next(make_session())
    add_event(session, event_id="event-1", event_type="deal.created", published_at=NOW)
    producer = FakeProducer()
    publisher = OutboxPublisher(
        repository=DomainEventsRepository(session),
        producer=producer,
        topic="dealmoa.domain-events",
        now=lambda: NOW + timedelta(minutes=1),
    )

    published_count = asyncio.run(publisher.publish_batch(limit=10))

    assert published_count == 0
    assert producer.messages == []
