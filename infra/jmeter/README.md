# DealMoa JMeter Baseline

This directory contains the first repeatable load-test baseline for DealMoa's public
search and ranking APIs.

## Scenario

`dealmoa-search-baseline.jmx` exercises:

- `GET /health`
- `GET /api/v1/search/products?q=<query>&limit=<limit>`
- `GET /api/v1/search/deals/hot?limit=<limit>`
- `GET /api/v1/search/auctions/activity?limit=<limit>`

The baseline is intentionally small. It proves that the test flow, result file, and
observability wiring exist before we tune real p95 targets.

## Local Docker Compose Run

Start the API and required local services:

```bash
docker compose --profile core up -d
```

Run the baseline:

```bash
docker compose --profile core --profile loadtest run --rm jmeter
```

Generated files:

- `infra/jmeter/results/dealmoa-search-baseline.jtl`
- `infra/jmeter/results/jmeter.log`

## Runtime Variables

The Docker Compose runner maps these environment variables into JMeter properties:

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

For a local API running outside Docker, use the host gateway from inside the JMeter
container:

```bash
JMETER_API_BASE_URL=http://host.docker.internal:8000 \
docker compose --profile loadtest run --rm jmeter
```

For a later Railway deployment, point `JMETER_API_BASE_URL` at the deployed API origin.
Do not include secrets in the JMeter plan or result files.

## Reading Results

The `.jtl` file is CSV. Useful first checks:

- `success=true` ratio should stay high.
- `elapsed` is request latency in milliseconds.
- `label` shows which endpoint sampler produced the row.
- `responseCode` shows whether failures are API errors, unavailable dependencies, or
  network problems.

Search and ranking endpoints require Elasticsearch indexes to exist. A fresh local stack
may need migrations, seed data, and an admin reindex before this baseline is meaningful.
