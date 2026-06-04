# Observability

## Stack

- Prometheus for metrics collection.
- Grafana for dashboards.

## Local Docker Compose Profile

Local observability runs through the `observability` Docker Compose profile:

```bash
docker compose --profile core --profile observability up
```

Local URLs:

- API metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

Environment variables:

```env
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=replace-with-local-grafana-password
```

Prometheus scrapes:

- `prometheus:9090`
- `api:8000/metrics`

Grafana provisioning:

- datasource: Prometheus at `http://prometheus:9090`
- dashboard: `DealMoa API Overview`

The first dashboard is intentionally small. It covers API request rate, 5xx ratio, and
p95 latency from the API metrics MVP. It is a local skeleton for development and demo
visibility, not a production monitoring setup.

## API Metrics MVP

FastAPI exposes Prometheus-compatible text metrics at:

```http
GET /metrics
```

Runtime setting:

```env
API_METRICS_ENABLED=true
```

Set `API_METRICS_ENABLED=false` to disable the endpoint. In public deployments, expose
`/metrics` only through a protected network path or platform access control; it contains
endpoint names, status-code counts, latency buckets, and default Python/process metrics.

The initial API middleware records:

- `dealmoa_api_http_requests_total`
  - type: counter
  - labels: `method`, `path`, `status_code`
  - purpose: request volume and error-rate calculation
- `dealmoa_api_http_request_duration_seconds`
  - type: histogram
  - labels: `method`, `path`
  - purpose: p95/p99 latency calculation

Path labels use route templates when FastAPI has matched a route. For example,
`/api/v1/products/{product_id}` is recorded instead of a concrete product id. This keeps
metric cardinality bounded. Unmatched routes use the raw request path because there is no
route template.

`/metrics` scrape requests are excluded from these request metrics so Prometheus scrapes
do not inflate API traffic numbers.

Current non-goals:

- alert rules;
- worker, consumer, Kafka, Celery, Redis, PostgreSQL, and Elasticsearch metrics;
- business metric counters beyond request traffic and latency.

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
