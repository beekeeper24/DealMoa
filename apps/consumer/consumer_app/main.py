import asyncio
import sys

from app.db.session import create_session_factory
from app.modules.events.repository import DomainEventsRepository
from app.modules.products.repository import ProductRepository
from app.modules.search.client import ElasticsearchSearchClient
from sqlalchemy.orm import Session

from consumer_app.config import ConsumerSettings
from consumer_app.domain_events import DomainEventSearchIndexer
from consumer_app.kafka import (
    DomainEventSubscriber,
    KafkaEventProducer,
    create_domain_event_consumer,
)
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


async def consume_search_index_forever(settings: ConsumerSettings) -> None:
    session_factory = create_session_factory(settings.database_url)
    consumer = create_domain_event_consumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_domain_events_topic,
        group_id=settings.kafka_search_index_group_id,
    )

    def handle_event(envelope: dict[str, object]) -> None:
        session: Session = session_factory()
        try:
            indexer = DomainEventSearchIndexer(
                product_repository=ProductRepository(session),
                search_client=ElasticsearchSearchClient(settings.elasticsearch_url),
            )
            indexer.handle(envelope)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    await DomainEventSubscriber(consumer=consumer, handler=handle_event).consume_forever()


def main() -> None:
    settings = ConsumerSettings()
    command = sys.argv[1] if len(sys.argv) > 1 else "publish-outbox"
    if command == "publish-outbox":
        asyncio.run(publish_forever(settings))
        return
    if command == "consume-search-index":
        asyncio.run(consume_search_index_forever(settings))
        return
    raise SystemExit(f"Unknown consumer command: {command}")


if __name__ == "__main__":
    main()
