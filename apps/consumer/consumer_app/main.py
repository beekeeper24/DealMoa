import asyncio

from app.db.session import create_session_factory
from app.modules.events.repository import DomainEventsRepository
from sqlalchemy.orm import Session

from consumer_app.config import ConsumerSettings
from consumer_app.kafka import KafkaEventProducer
from consumer_app.outbox_publisher import OutboxPublisher


async def publish_forever(settings: ConsumerSettings) -> None:
    session_factory = create_session_factory(settings.database_url)
    async with KafkaEventProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
    ) as producer:
        while True:
            session: Session = session_factory()
            try:
                publisher = OutboxPublisher(
                    repository=DomainEventsRepository(session),
                    producer=producer,
                    topic=settings.kafka_domain_events_topic,
                )
                await publisher.publish_batch(limit=settings.consumer_batch_size)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
            await asyncio.sleep(settings.consumer_poll_interval_seconds)


def main() -> None:
    asyncio.run(publish_forever(ConsumerSettings()))


if __name__ == "__main__":
    main()
