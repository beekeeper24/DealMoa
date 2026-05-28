from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


class EventProducer(Protocol):
    async def publish(self, *, topic: str, message: dict[str, object]) -> None:
        pass


class OutboxPublisher:
    def __init__(
        self,
        *,
        repository: DomainEventsRepository,
        producer: EventProducer,
        topic: str,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository
        self.producer = producer
        self.topic = topic
        self.now = now

    async def publish_batch(self, *, limit: int) -> int:
        events = self.repository.list_unpublished(limit=limit)
        published_count = 0
        for event in events:
            await self.producer.publish(topic=self.topic, message=self._message_for_event(event))
            self.repository.mark_published(event_id=event.id, published_at=self.now())
            published_count += 1
        return published_count

    def _message_for_event(self, event: DomainEvent) -> dict[str, object]:
        return {
            "eventId": event.id,
            "eventType": event.event_type,
            "aggregateType": event.aggregate_type,
            "aggregateId": event.aggregate_id,
            "payload": event.payload_json,
            "occurredAt": event.created_at.isoformat(),
        }
