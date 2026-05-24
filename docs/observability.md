# Observability

## Stack

- Prometheus for metrics collection.
- Grafana for dashboards.

## Dashboards

- API overview: RPS, p95/p99 latency, error rate, endpoint latency.
- Search and ranking: search latency, Elasticsearch query latency, zero-result rate, popular queries.
- Events and workers: Kafka consumer lag, event throughput, Celery task duration/failure/retry, indexing failures.

## Business Metrics

- Search count.
- AI search count.
- Hot-deal views.
- Auction views.
- Favorite count.
- Notification count.
- Submission/review approval queue size.
