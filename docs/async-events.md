# Async Events Foundation

This slice adds the first real Kafka/Celery code boundary while keeping product APIs coherent and locally testable.

## Scope

- API writes domain events to a transactional outbox table.
- `apps/consumer` polls unpublished outbox events and publishes them to Kafka.
- `apps/worker` exposes initial Celery task entry points.
- Docker Compose has separate `event` and `worker` profiles.

Out of scope:

- Elasticsearch indexing through Kafka consumers.
- Notification generation through Kafka consumers.
- Real crawler, AI review, embedding, or scheduled jobs.

## Transactional Outbox

The `domain_events` table stores API-side domain events in the same DB transaction as the domain mutation.

Initial event types:

| Event | Aggregate | Producer |
| --- | --- | --- |
| `product.updated` | `product` | Product API product create/update paths |
| `deal.created` | `deal` | Product API deal create path |
| `auction.created` | `auction` | Product API auction create path |

The outbox publisher sends messages with this envelope:

```json
{
  "eventId": "event-id",
  "eventType": "deal.created",
  "aggregateType": "deal",
  "aggregateId": "deal-id",
  "payload": {},
  "occurredAt": "2026-05-28T15:00:00+00:00"
}
```

`eventId` is the idempotency key for downstream consumers.

## Kafka Consumer Runtime

`apps/consumer` currently publishes outbox events to the configured Kafka topic.

Environment:

```text
DATABASE_URL=postgresql+psycopg://...
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_DOMAIN_EVENTS_TOPIC=dealmoa.domain-events
CONSUMER_POLL_INTERVAL_SECONDS=1
CONSUMER_BATCH_SIZE=100
```

Local runtime:

```bash
docker compose --profile core --profile event up --build
```

## Celery Worker Runtime

`apps/worker` currently registers mock tasks:

- `dealmoa.crawl_hot_deals_mock`
- `dealmoa.ai_review_submission_mock`
- `dealmoa.rebuild_search_index`

Environment:

```text
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

Local runtime:

```bash
docker compose --profile core --profile worker up --build
```

## Next Steps

- Move Elasticsearch index synchronization behind Kafka events.
- Move product favorite notification generation behind `deal.created` and `auction.created`.
- Add Celery beat for scheduled auction-ending notification jobs.
- Add idempotent consumer tables when consumers begin producing side effects.
