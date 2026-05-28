import json
from collections.abc import AsyncIterator, Callable
from typing import Any, Protocol, cast

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer  # type: ignore[import-untyped]


class KafkaEventProducer:
    def __init__(self, *, bootstrap_servers: str) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    async def __aenter__(self) -> "KafkaEventProducer":
        await self.producer.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.producer.stop()

    async def publish(self, *, topic: str, message: dict[str, object]) -> None:
        key = str(message["eventId"]).encode("utf-8")
        await self.producer.send_and_wait(topic, value=message, key=key)


class KafkaMessage(Protocol):
    value: bytes


class DomainEventConsumer(Protocol):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def __aiter__(self) -> AsyncIterator[KafkaMessage]:
        pass


class DomainEventSubscriber:
    def __init__(
        self,
        *,
        consumer: DomainEventConsumer,
        handler: Callable[[dict[str, Any]], object],
    ) -> None:
        self.consumer = consumer
        self.handler = handler

    async def consume_forever(self) -> None:
        await self.consumer.start()
        try:
            async for message in self.consumer:
                envelope = self._decode_message(message.value)
                if envelope is not None:
                    self.handler(envelope)
        finally:
            await self.consumer.stop()

    def _decode_message(self, value: bytes) -> dict[str, Any] | None:
        try:
            decoded = json.loads(value.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None
        return decoded


def create_domain_event_consumer(
    *,
    bootstrap_servers: str,
    topic: str,
    group_id: str,
) -> DomainEventConsumer:
    return cast(
        DomainEventConsumer,
        AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            enable_auto_commit=True,
            auto_offset_reset="earliest",
        ),
    )
