import json

from aiokafka import AIOKafkaProducer  # type: ignore[import-untyped]


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
