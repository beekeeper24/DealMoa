# Local Demo Smoke - 2026-06-05

## Summary

- Issue: [#94](https://github.com/beekeeper24/DealMoa/issues/94)
- Branch: `feature/full-local-demo-smoke`
- Compose project: `dealmoa_smoke`
- Decision: local full demo smoke passed after fixing runtime blockers found during the smoke.

This smoke used real Docker Compose services instead of mocked frontend tests. It verifies
that the MVP can move to the first Vercel/Railway deployment setup.

## Isolated Local Runtime

Default local ports were already used by other projects, so this run used shifted host
ports:

| Service | Local URL |
| --- | --- |
| API | `http://localhost:18002` |
| Web | `http://localhost:13002` |
| PostgreSQL | `localhost:15435` |
| Redis | `localhost:16381` |
| Elasticsearch | `http://localhost:19202` |
| Kafka/Redpanda | `localhost:19092`, admin `http://localhost:19644` |
| Consumer metrics | `http://localhost:19101/metrics` |
| Worker metrics | `http://localhost:19102/metrics` |
| Prometheus | `http://localhost:19090` |
| Grafana | `http://localhost:13003` |

Core startup:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
POSTGRES_PORT=15435 \
REDIS_PORT=16381 \
ELASTICSEARCH_PORT=19202 \
API_PORT=18002 \
WEB_PORT=13002 \
API_CORS_ORIGINS=http://localhost:13002 \
NEXT_PUBLIC_API_BASE_URL=http://localhost:18002/api/v1 \
WEB_PUBLIC_API_BASE_URL=http://localhost:18002/api/v1 \
docker compose --profile core up -d --build
```

Migration:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
POSTGRES_PORT=15435 \
REDIS_PORT=16381 \
ELASTICSEARCH_PORT=19202 \
API_PORT=18002 \
WEB_PORT=13002 \
docker compose --profile core exec -T -w /workspace api \
  /workspace/.venv/bin/alembic -c apps/api/alembic.ini upgrade head
```

Korean demo seed and reindex:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
POSTGRES_PORT=15435 \
REDIS_PORT=16381 \
ELASTICSEARCH_PORT=19202 \
API_PORT=18002 \
WEB_PORT=13002 \
docker compose --profile core exec -T api \
  /workspace/.venv/bin/python -m app.modules.demo_seed.cli --reindex
```

Seed result:

```json
{
  "products_created": 6,
  "deals_created": 6,
  "auctions_created": 6,
  "users_created": 4,
  "auction_bids_created": 15,
  "deal_favorites_created": 15,
  "auction_favorites_created": 9,
  "reindex": {
    "products": 6,
    "deals": 6,
    "auctions": 6
  }
}
```

Full runtime startup:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
POSTGRES_PORT=15435 \
REDIS_PORT=16381 \
ELASTICSEARCH_PORT=19202 \
API_PORT=18002 \
WEB_PORT=13002 \
KAFKA_PORT=19092 \
REDPANDA_ADMIN_PORT=19644 \
CONSUMER_METRICS_HOST_PORT=19101 \
WORKER_METRICS_HOST_PORT=19102 \
PROMETHEUS_PORT=19090 \
GRAFANA_PORT=13003 \
API_CORS_ORIGINS=http://localhost:13002 \
NEXT_PUBLIC_API_BASE_URL=http://localhost:18002/api/v1 \
WEB_PUBLIC_API_BASE_URL=http://localhost:18002/api/v1 \
docker compose --profile core --profile event --profile worker --profile observability up -d --build
```

## Fixes Made During Smoke

- `grafana/grafana-oss:12.3.0` did not exist on Docker Hub. Changed the local Compose
  image to verified tag `grafana/grafana-oss:12.1.1`.
- `apps/consumer` and `apps/worker` were using `uv run` as runtime commands. They failed
  as the non-root container user because uv tried to create `/nonexistent/.cache/uv`.
  Dockerfile and Compose commands now call `/workspace/.venv/bin/...` directly.
- `CONSUMER_METRICS_PORT` and `WORKER_METRICS_PORT` were being used as both container
  listen ports and host ports. Added `CONSUMER_METRICS_HOST_PORT` and
  `WORKER_METRICS_HOST_PORT` so host ports can move without breaking Prometheus'
  internal `consumer:9101` and `worker:9102` targets.
- `apps/consumer` imported API search code that needs `httpx`; `apps/worker` imported API
  auth code that needs `PyJWT`. Added those package dependencies and updated `uv.lock`.

## API Smoke

All checked API endpoints returned HTTP 200 after migration and seed.

Public checks:

- `GET /health`
- `GET /api/v1/health`
- `GET /metrics`
- `GET /api/v1/search/products?q=갤럭시&limit=3`
- `GET /api/v1/search/deals/hot?limit=3`
- `GET /api/v1/search/auctions/activity?limit=3`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/products/{product_id}/deals`
- `GET /api/v1/products/{product_id}/auctions`
- `GET /api/v1/deals/{deal_id}`
- `GET /api/v1/auctions/{auction_id}`
- `GET /api/v1/products/{product_id}/price-history`
- `GET /api/v1/products/{product_id}/verified-reviews`
- `GET /api/v1/products/{product_id}/discussions`
- `GET /api/v1/ai/products/{product_id}/purchase-check`
- `POST /api/v1/ai/search`

Authenticated checks used local-only generated JWTs. Token values were not printed.

- `GET /api/v1/auth/me`
- `GET /api/v1/me/submissions`
- `GET /api/v1/me/verified-reviews`
- `GET /api/v1/notifications`
- `GET /api/v1/notifications/unread-count`

Admin checks used a local-only `demo-admin` user in the smoke database.

- `GET /api/v1/admin/reports`
- `GET /api/v1/admin/submissions`
- `GET /api/v1/admin/verified-reviews`
- `GET /api/v1/admin/discussions`
- `GET /api/v1/admin/crawler-runs`

Notes:

- Korean product search for `갤럭시` returned the seeded Samsung product.
- AI search for `갤럭시` returned product, deal, and auction candidates.
- AI search for the longer sentence `갤럭시 S26 싸게 사고 싶어` returned zero candidates
  with the current mock intent behavior. This is not a deployment blocker, but it is a
  tuning candidate before a polished demo.
- Price history, verified review, discussion, submission, notification, report, and admin
  queues were empty in the local seed. Empty HTTP 200 lists are expected for this seed.

## Worker, Consumer, And Observability Smoke

Container status after fixes:

- `api`: up on `18002`
- `web`: up on `13002`
- `postgres`: healthy on `15435`
- `redis`: healthy on `16381`
- `elasticsearch`: healthy on `19202`
- `kafka`: healthy on `19092`
- `consumer`: up, host metrics `19101 -> 9101`
- `worker`: up, host metrics `19102 -> 9102`
- `prometheus`: up on `19090`
- `grafana`: up on `13003`

Metrics checks:

- `GET http://localhost:19101/metrics`: consumer Prometheus text exposed.
- `GET http://localhost:19102/metrics`: worker Prometheus text exposed.
- Prometheus targets: `dealmoa-api`, `dealmoa-consumer`, `dealmoa-worker`, and
  `prometheus` all `up`.
- Grafana health: database `ok`, version `12.1.1`.

## Web Smoke

Playwright opened the Docker web runtime at `http://localhost:13002`.

Pages checked:

- `/`
- `/products/{product_id}`
- `/deals/{deal_id}`
- `/auctions/{auction_id}`
- `/submit`
- `/me`
- `/admin`
- `/admin/submissions`
- `/admin/verified-reviews`
- `/admin/discussions`
- `/admin/crawler-runs`

Result:

- All pages returned HTTP 200.
- No Playwright `pageerror` occurred.
- Public detail pages rendered seeded Korean product/deal/auction data.
- Protected pages rendered login-required or admin-required states.
- Browser console included expected 401 resource messages from unauthenticated
  `/auth/me` or protected API checks. The UI handled these as login-required states.

## Verification

Passed:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
CONSUMER_METRICS_HOST_PORT=19101 \
WORKER_METRICS_HOST_PORT=19102 \
docker compose --profile core --profile event --profile worker --profile observability config --quiet
```

Passed:

```bash
PYTHONPATH=apps/consumer:apps/worker:apps/api \
uv run pytest apps/consumer/tests apps/worker/tests
```

Result: `57 passed in 14.55s`.

The first test attempt without `PYTHONPATH` failed during collection because pytest could
not import `consumer_app`, `worker_app`, or `app`. That was a command-shape issue, not a
runtime/code failure.

## Cleanup

The smoke containers were left running during verification. To stop them without deleting
volumes:

```bash
COMPOSE_PROJECT_NAME=dealmoa_smoke \
POSTGRES_PORT=15435 \
REDIS_PORT=16381 \
ELASTICSEARCH_PORT=19202 \
API_PORT=18002 \
WEB_PORT=13002 \
KAFKA_PORT=19092 \
REDPANDA_ADMIN_PORT=19644 \
CONSUMER_METRICS_HOST_PORT=19101 \
WORKER_METRICS_HOST_PORT=19102 \
PROMETHEUS_PORT=19090 \
GRAFANA_PORT=13003 \
docker compose --profile core --profile event --profile worker --profile observability down
```

Use `--volumes` only when intentionally deleting the smoke database, search index, Kafka
data, Prometheus data, and Grafana data.

## Next Step

Proceed to first deployment setup:

1. Configure Vercel web project rooted at `apps/web`.
2. Configure Railway API service and backing service variables.
3. Keep Railway worker/consumer disabled until Redis/Kafka/backing-service decisions are
   ready for deployed async runtime.
4. Run deployed smoke after Vercel/Railway are connected.
