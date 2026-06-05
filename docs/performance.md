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
