# Observability

## Stack

- Prometheus for metrics collection.
- Grafana for dashboards.

## Local Docker Compose Profile

Local observability runs through the `observability` Docker Compose profile:

```bash
docker compose --profile core --profile observability up
```

Background worker/consumer metrics need their runtimes too:

```bash
docker compose --profile core --profile event --profile worker --profile observability up
```

Local URLs:

- API metrics: `http://localhost:8000/metrics`
- Consumer metrics: `http://localhost:9101/metrics`
- Worker metrics: `http://localhost:9102/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

Environment variables:

```env
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=replace-with-local-grafana-password
CONSUMER_METRICS_ENABLED=true
CONSUMER_METRICS_PORT=9101
CONSUMER_METRICS_HOST_PORT=9101
WORKER_METRICS_ENABLED=true
WORKER_METRICS_PORT=9102
WORKER_METRICS_HOST_PORT=9102
```

Prometheus scrapes:

- `prometheus:9090`
- `api:8000/metrics`
- `consumer:9101`
- `worker:9102`

`CONSUMER_METRICS_PORT` and `WORKER_METRICS_PORT` are the container listen ports. Keep
them at `9101` and `9102` for the local Prometheus config unless the Prometheus target
config changes too. Use `CONSUMER_METRICS_HOST_PORT` and `WORKER_METRICS_HOST_PORT` when
only the local host ports need to move because another project already uses the defaults.

Grafana provisioning:

- datasource: Prometheus at `http://prometheus:9090`
- dashboard: `DealMoa Runtime Overview`

The first dashboard is intentionally small. It covers API request rate, 5xx ratio, p95
latency, consumer event throughput, and worker task throughput. It is a local skeleton
for development and demo visibility, not a production monitoring setup.

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
- Kafka lag exporters, Celery retry metrics, Redis/PostgreSQL/Elasticsearch exporters;
- business metric counters beyond current API/background runtime visibility.

## Background Runtime Metrics MVP

`apps/consumer` starts a small Prometheus metrics server when:

```env
CONSUMER_METRICS_ENABLED=true
```

It records:

- `dealmoa_consumer_events_total`
  - type: counter
  - labels: `consumer`, `event_type`, `status`
  - statuses: `handled`, `skipped`, `failed`
  - purpose: see whether event consumers are handling, skipping, or failing messages.

`apps/worker` starts a small Prometheus metrics server when:

```env
WORKER_METRICS_ENABLED=true
```

It records:

- `dealmoa_worker_tasks_total`
  - type: counter
  - labels: `status`, `task`
  - statuses: `succeeded`, `failed`
  - purpose: see Celery task completion/failure volume.
- `dealmoa_worker_task_duration_seconds`
  - type: histogram
  - labels: `task`
  - purpose: see task duration distribution.

The local Docker Compose worker uses Celery `--pool=solo` so task execution and metrics
collection run in the same process. Production Celery multiprocess metrics need a
dedicated Prometheus multiprocess setup or a separate exporter before enabling the same
approach outside local development.

## Dashboards

- API overview: RPS, p95/p99 latency, error rate, endpoint latency.
- Search and ranking: search latency, Elasticsearch query latency, zero-result rate, popular queries.
- Events and workers: event throughput, Celery task duration/failure, Kafka consumer lag, retry rate, indexing failures.

## Business Metrics

- Search count.
- AI search count.
- Hot-deal views.
- Auction views.
- Favorite count.
- Notification count.
- Submission/review approval queue size.
