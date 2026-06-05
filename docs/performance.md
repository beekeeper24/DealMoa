# Performance

## Load-Test Tool

- Apache JMeter.

## JMeter Baseline

The first repeatable JMeter baseline lives at:

```text
infra/jmeter/dealmoa-search-baseline.jmx
```

It exercises:

- `GET /health`
- `GET /api/v1/search/products?q=<query>&limit=<limit>`
- `GET /api/v1/search/deals/hot?limit=<limit>`
- `GET /api/v1/search/auctions/activity?limit=<limit>`

Local Docker Compose command:

```bash
docker compose --profile core --profile loadtest run --rm jmeter
```

For meaningful local results, prepare Korean demo data first:

```bash
docker compose --profile core up -d
docker compose --profile core exec api uv run python -m app.modules.demo_seed.cli --reindex
docker compose --profile core --profile loadtest run --rm jmeter
```

The runner writes:

- `infra/jmeter/results/dealmoa-search-baseline.jtl`
- `infra/jmeter/results/jmeter.log`

Summarize the CSV result after a run:

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl
```

For automation or later comparison scripts, use JSON output:

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl --json
```

The summary reports total and per-endpoint request count, success count, failure count,
error rate, average latency, p95 latency, and max latency. It is a local reading aid,
not a CI performance gate.

## Local Baseline Observation - 2026-06-05

This observation used local WSL Docker Compose with a fresh isolated Compose project
named `dealmoa_perf`. Host ports were shifted because other local projects already used
PostgreSQL, Redis, and Elasticsearch default ports.

Runtime preparation:

```bash
COMPOSE_PROJECT_NAME=dealmoa_perf \
POSTGRES_PORT=15434 \
REDIS_PORT=16380 \
ELASTICSEARCH_PORT=19201 \
API_PORT=18001 \
WEB_PORT=13001 \
docker compose --profile core up -d

COMPOSE_PROJECT_NAME=dealmoa_perf \
POSTGRES_PORT=15434 \
REDIS_PORT=16380 \
ELASTICSEARCH_PORT=19201 \
API_PORT=18001 \
WEB_PORT=13001 \
docker compose --profile core exec -w /workspace api \
  /workspace/.venv/bin/alembic -c apps/api/alembic.ini upgrade head

COMPOSE_PROJECT_NAME=dealmoa_perf \
POSTGRES_PORT=15434 \
REDIS_PORT=16380 \
ELASTICSEARCH_PORT=19201 \
API_PORT=18001 \
WEB_PORT=13001 \
docker compose --profile core exec api \
  /workspace/.venv/bin/python -m app.modules.demo_seed.cli --reindex
```

Seed and reindex result:

```json
{"reindex": {"auctions": 6, "deals": 6, "products": 6}, "seed": {"auction_bids_created": 15, "auction_favorites_created": 9, "auctions_created": 6, "deal_favorites_created": 15, "deals_created": 6, "products_created": 6, "users_created": 4}}
```

JMeter run:

```bash
COMPOSE_PROJECT_NAME=dealmoa_perf \
POSTGRES_PORT=15434 \
REDIS_PORT=16380 \
ELASTICSEARCH_PORT=19201 \
API_PORT=18001 \
WEB_PORT=13001 \
JMETER_SEARCH_QUERY=갤럭시 \
docker compose --profile core --profile loadtest run --rm jmeter
```

JMeter settings:

- `JMETER_THREADS=5`
- `JMETER_RAMP_SECONDS=30`
- `JMETER_DURATION_SECONDS=60`
- `JMETER_SEARCH_QUERY=갤럭시`
- `JMETER_SEARCH_LIMIT=10`
- `JMETER_THINK_TIME_MS=250`

Summary:

```text
JMeter Summary
overall: count=897 success=897 failure=0 error_rate=0.00% avg=16.3ms p95=32ms max=88ms
by label:
- GET auction activity ranking: count=222 success=222 failure=0 error_rate=0.00% avg=20.0ms p95=32ms max=82ms
- GET hot deals ranking: count=224 success=224 failure=0 error_rate=0.00% avg=20.2ms p95=33ms max=68ms
- GET product search: count=225 success=225 failure=0 error_rate=0.00% avg=21.2ms p95=34ms max=73ms
- GET root health: count=226 success=226 failure=0 error_rate=0.00% avg=3.7ms p95=10ms max=88ms
```

Interpretation:

- This confirms the JMeter flow, local API runtime, Korean demo seed, Elasticsearch
  reindex, and summary script work together end-to-end.
- The measured search/ranking p95 values are local demo observations only. They are not
  production SLOs and should not be used as CI failure thresholds yet.
- The dataset is intentionally tiny: 6 products, 6 deals, 6 auctions, 15 auction bids,
  and favorite signals. Larger or production-like data can change latency materially.
- The first local run exposed an invalid JMeter response assertion. The plan now asserts
  HTTP `200` correctly so successful API responses are not counted as JMeter failures.

Configurable variables:

```env
JMETER_API_BASE_URL=http://api:8000
JMETER_API_PREFIX=/api/v1
JMETER_THREADS=5
JMETER_RAMP_SECONDS=30
JMETER_DURATION_SECONDS=60
JMETER_SEARCH_QUERY=Galaxy
JMETER_SEARCH_LIMIT=10
JMETER_THINK_TIME_MS=250
```

The baseline is small by design. It checks repeatability and observability readiness
before real tuning. Meaningful search/ranking numbers require initialized Elasticsearch
indexes, representative data, and an API runtime similar to the environment being
measured.

The demo seed data intentionally uses Korean product names, categories, deal titles,
auction titles, and specs because DealMoa search quality depends on Korean/Nori behavior.

## Frontend Verification

- Add Playwright as soon as the frontend app is introduced.
- Use it first for smoke checks in CI: app loads, top search bar renders, API health state is visible.
- Current browser smoke coverage includes search results, AI search entry, favorites,
  OAuth callback hydration, product detail, AI purchase check, verified-review submission
  success and duplicate error handling, auction bidding, My Page, user submissions, and
  admin queues.
- Expand it later to cover mobile layout, visual regression, notification history page,
  and real backend integration smoke checks.

## Scenarios

- Hot-deal spike: many users view and favorite a newly popular deal.
- Auction ending spike: many users view an auction near closing time.
- Search peak: concurrent general search and tab switching for popular terms.

## Initial Goals

- Search API p95 latency target should be measured and tuned after baseline.
- Error rate should remain below an agreed threshold under demo load.
- Kafka consumer lag should recover after spikes.
- Elasticsearch indexing delay should remain visible and measurable.

## Current Non-Goals

- Production SLOs.
- Long-running soak tests.
- CI-gated performance thresholds.
- Automatic Grafana alert rules.
- Tuning Elasticsearch, DB indexes, or worker concurrency from the first baseline.
