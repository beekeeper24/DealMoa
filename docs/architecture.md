# Architecture

## Components

- Next.js/React: user/admin UI.
- FastAPI: REST API, auth, validation, DB transactions, outbox creation.
- PostgreSQL: source of truth.
- Elasticsearch: search and ranking read models.
- Kafka: domain event stream.
- Celery + Redis: background jobs and scheduled Python work.
- Prometheus/Grafana: metrics and dashboards.
- JMeter: load-test scenarios.

## Async Boundary

Kafka is for events:

- `deal.created`
- `auction.created`
- `product.updated`
- `favorite.created`
- `review.verified`

Celery is for jobs:

- crawling
- AI review
- embedding generation
- scheduled auction/deal checks
- long-running data processing

Do not let Kafka consumers and Celery tasks produce the same side effect.
