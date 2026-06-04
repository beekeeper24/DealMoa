import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import pytest
from consumer_app.kafka import DomainEventSubscriber
from consumer_app.metrics import ConsumerMetrics
from prometheus_client import CollectorRegistry


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


def test_domain_event_subscriber_records_handled_event_metrics() -> None:
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
    metrics = ConsumerMetrics(registry=CollectorRegistry())
    subscriber = DomainEventSubscriber(
        consumer=consumer,
        handler=lambda envelope: None,
        consumer_name="search-index",
        metrics=metrics,
    )

    asyncio.run(subscriber.consume_forever())
    expected_sample = (
        'dealmoa_consumer_events_total{consumer="search-index",'
        'event_type="deal.created",status="handled"} 1.0'
    )

    assert expected_sample in metrics.generate().decode("utf-8")


def test_domain_event_subscriber_records_skipped_event_metrics() -> None:
    consumer = FakeConsumer([FakeKafkaMessage(b"not-json")])
    metrics = ConsumerMetrics(registry=CollectorRegistry())
    subscriber = DomainEventSubscriber(
        consumer=consumer,
        handler=lambda envelope: None,
        consumer_name="search-index",
        metrics=metrics,
    )

    asyncio.run(subscriber.consume_forever())
    expected_sample = (
        'dealmoa_consumer_events_total{consumer="search-index",'
        'event_type="unknown",status="skipped"} 1.0'
    )

    assert expected_sample in metrics.generate().decode("utf-8")


def test_domain_event_subscriber_records_failed_event_metrics() -> None:
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
    metrics = ConsumerMetrics(registry=CollectorRegistry())

    def raise_error(envelope: dict[str, Any]) -> None:
        raise RuntimeError("handler failed")

    subscriber = DomainEventSubscriber(
        consumer=consumer,
        handler=raise_error,
        consumer_name="search-index",
        metrics=metrics,
    )

    with pytest.raises(RuntimeError, match="handler failed"):
        asyncio.run(subscriber.consume_forever())

    assert consumer.stopped is True
    expected_sample = (
        'dealmoa_consumer_events_total{consumer="search-index",'
        'event_type="deal.created",status="failed"} 1.0'
    )
    assert expected_sample in metrics.generate().decode("utf-8")
