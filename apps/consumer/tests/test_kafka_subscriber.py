import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from consumer_app.kafka import DomainEventSubscriber


@dataclass
class FakeKafkaMessage:
    value: bytes


class FakeConsumer:
    def __init__(self, messages: list[FakeKafkaMessage]) -> None:
        self.messages = messages
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def __aiter__(self) -> AsyncIterator[FakeKafkaMessage]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[FakeKafkaMessage]:
        for message in self.messages:
            yield message


def test_domain_event_subscriber_dispatches_json_messages() -> None:
    consumer = FakeConsumer(
        [
            FakeKafkaMessage(
                json.dumps(
                    {
                        "eventId": "event-1",
                        "eventType": "deal.created",
                        "aggregateType": "deal",
                        "aggregateId": "deal-1",
                        "payload": {"dealId": "deal-1"},
                        "occurredAt": "2026-05-28T16:00:00Z",
                    }
                ).encode("utf-8")
            )
        ]
    )
    handled: list[dict[str, Any]] = []
    subscriber = DomainEventSubscriber(consumer=consumer, handler=handled.append)

    asyncio.run(subscriber.consume_forever())

    assert consumer.started is True
    assert consumer.stopped is True
    assert handled == [
        {
            "eventId": "event-1",
            "eventType": "deal.created",
            "aggregateType": "deal",
            "aggregateId": "deal-1",
            "payload": {"dealId": "deal-1"},
            "occurredAt": "2026-05-28T16:00:00Z",
        }
    ]


def test_domain_event_subscriber_skips_invalid_json_messages() -> None:
    consumer = FakeConsumer([FakeKafkaMessage(b"not-json")])
    handled: list[dict[str, Any]] = []
    subscriber = DomainEventSubscriber(consumer=consumer, handler=handled.append)

    asyncio.run(subscriber.consume_forever())

    assert handled == []
