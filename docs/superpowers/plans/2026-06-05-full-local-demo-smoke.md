# Full Local Demo Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run DealMoa's real local API/Web runtime with backing services and record whether the MVP is coherent enough to proceed to Vercel/Railway deployment setup.

**Architecture:** Use an isolated Docker Compose project named `dealmoa_smoke` with shifted host ports so existing local containers are not disturbed. Verify the runtime through real migrations, Korean demo seed data, Elasticsearch reindexing, public API checks, authenticated/admin API checks with local generated tokens, and web page smoke checks. Record commands, results, blockers, and next deployment readiness steps in local docs and the Notion work log.

**Tech Stack:** Docker Compose, FastAPI, PostgreSQL, Redis, Elasticsearch/Nori, Kafka/Redpanda, Celery, Next.js, Playwright or curl-based browser smoke, GitHub Issues/PRs.

---

### Task 1: Tracking And Branch Setup

**Files:**
- Create: `docs/superpowers/plans/2026-06-05-full-local-demo-smoke.md`
- Create later: `docs/local-demo-smoke-2026-06-05.md`
- Modify later: `docs/handoff.md`

- [ ] **Step 1: Create a GitHub Task issue**

Run:

```bash
gh issue create \
  --title "[Task] Full local demo smoke 실행 및 결과 기록" \
  --label task \
  --body-file /tmp/dealmoa-full-local-demo-smoke-issue.md
```

Expected: GitHub returns an issue URL. The issue acceptance criteria include isolated Compose startup, migrations, Korean seed/reindex, API smoke, web smoke, worker/consumer/observability checks, and documentation.

- [ ] **Step 2: Sync `develop`**

Run:

```bash
git checkout develop
git pull --ff-only origin develop
```

Expected: local `develop` matches `origin/develop`.

- [ ] **Step 3: Create the feature branch**

Run:

```bash
git checkout -b feature/full-local-demo-smoke
```

Expected: `git status --short --branch` shows `## feature/full-local-demo-smoke`.

### Task 2: Isolated Runtime Startup

**Files:**
- Read: `docker-compose.yml`
- Read: `.env.example`
- Do not read or print secret values from `.env`

- [ ] **Step 1: Start core services with shifted ports**

Run:

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

Expected: PostgreSQL, Redis, Elasticsearch, API, and Web containers start without colliding with existing local containers.

- [ ] **Step 2: Run Alembic migrations inside the API container**

Run:

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
docker compose --profile core exec -T -w /workspace api \
  /workspace/.venv/bin/alembic -c apps/api/alembic.ini upgrade head
```

Expected: Alembic applies all migrations successfully.

- [ ] **Step 3: Seed Korean demo data and rebuild Elasticsearch indexes**

Run:

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
docker compose --profile core exec -T api \
  /workspace/.venv/bin/python -m app.modules.demo_seed.cli --reindex
```

Expected: Korean demo products, deals, auctions, users, bids, favorites, price history, and reviews are present, and search indexes are rebuilt.

### Task 3: API Smoke

**Files:**
- Read: `apps/api/app/api/v1/router.py`
- Read relevant routers under `apps/api/app/modules/**/router.py`
- Create later: `docs/local-demo-smoke-2026-06-05.md`

- [ ] **Step 1: Verify public health and metrics**

Run:

```bash
curl -fsS http://localhost:18002/health
curl -fsS http://localhost:18002/metrics | head
```

Expected: health returns an OK payload, and metrics include Prometheus text output.

- [ ] **Step 2: Verify Korean search and ranking endpoints**

Run:

```bash
curl -fsS "http://localhost:18002/api/v1/search/products?q=갤럭시&limit=3"
curl -fsS "http://localhost:18002/api/v1/search/deals/hot?limit=3"
curl -fsS "http://localhost:18002/api/v1/search/auctions/activity?limit=3"
```

Expected: each endpoint returns seeded Korean demo results.

- [ ] **Step 3: Verify product detail, price history, verified reviews, discussions, and AI assistant public flows**

Use IDs returned from search results.

Expected: public detail and evidence endpoints return coherent data; AI assistant stays on mock provider unless the environment explicitly enables OpenAI.

- [ ] **Step 4: Verify authenticated and admin flows with local generated tokens**

Generate local-only JWTs inside the API container for seeded demo users without printing `.env` values.

Expected: `/api/v1/auth/me`, `/api/v1/me/*`, `/api/v1/notifications`, and `/api/v1/admin/*` queues respond with expected data or empty lists, not auth/config errors.

### Task 4: Worker, Consumer, And Observability Smoke

**Files:**
- Read: `docker-compose.yml`
- Read: `infra/prometheus/prometheus.yml`
- Read: `infra/grafana/**`

- [ ] **Step 1: Start event, worker, and observability profiles with shifted ports**

Run:

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

Expected: Redpanda, consumer, worker, worker-beat, Prometheus, and Grafana start without port conflicts.

- [ ] **Step 2: Verify metrics surfaces**

Run:

```bash
curl -fsS http://localhost:19101/metrics | head
curl -fsS http://localhost:19102/metrics | head
curl -fsS "http://localhost:19090/api/v1/targets"
curl -fsS http://localhost:13003/api/health
```

Expected: consumer/worker metrics expose Prometheus text; Prometheus targets include API, consumer, and worker; Grafana health is OK.

### Task 5: Web Smoke

**Files:**
- Read: `apps/web/package.json`
- Create later: `docs/local-demo-smoke-2026-06-05.md`

- [ ] **Step 1: Verify web home and public pages load against the shifted API**

Run curl or Playwright against:

```text
http://localhost:13002/
http://localhost:13002/products/<product-id>
http://localhost:13002/deals/<deal-id>
http://localhost:13002/auctions/<auction-id>
```

Expected: pages return HTML and do not show obvious runtime errors.

- [ ] **Step 2: Verify authenticated/admin pages have coherent unauthenticated behavior**

Run curl or Playwright against:

```text
http://localhost:13002/me
http://localhost:13002/submit
http://localhost:13002/admin
http://localhost:13002/admin/submissions
http://localhost:13002/admin/verified-reviews
http://localhost:13002/admin/discussions
http://localhost:13002/admin/crawler-runs
```

Expected: pages load and show login-required or admin-required state without crashing. Deep authenticated UI login is deferred to deployed OAuth/browser testing unless local OAuth callbacks are configured.

### Task 6: Documentation, Commit, PR, And Merge

**Files:**
- Create: `docs/local-demo-smoke-2026-06-05.md`
- Modify: `docs/handoff.md`
- Modify if commands need clarification: `docs/release-readiness.md`

- [ ] **Step 1: Document the local smoke result**

Record:

```text
date, branch, compose project, shifted ports, exact commands, checked endpoints, pass/fail results, blockers, cleanup command, next deployment step
```

Expected: a future session can rerun the same local smoke without guessing.

- [ ] **Step 2: Update handoff**

Expected: `docs/handoff.md` says whether full local demo smoke passed, and points to the result doc.

- [ ] **Step 3: Run completion verification**

Run:

```bash
git status --short
```

Expected: only intended docs and any necessary small fixes are changed.

- [ ] **Step 4: Commit, push, open PR, wait for CI, merge into `develop`**

Run:

```bash
git add docs/superpowers/plans/2026-06-05-full-local-demo-smoke.md docs/local-demo-smoke-2026-06-05.md docs/handoff.md
git commit -m "docs: 로컬 데모 스모크 결과 기록"
git push -u origin feature/full-local-demo-smoke
gh pr create --base develop --head feature/full-local-demo-smoke --title "docs: 로컬 데모 스모크 결과 기록" --body-file /tmp/dealmoa-full-local-demo-smoke-pr.md
```

Expected: PR targets `develop`. Merge only after local verification and required CI/review checks are acceptable.

---

## Self-Review

- Spec coverage: The plan covers the requested release-readiness next step: full local API/Web runtime smoke before deployment setup.
- Placeholder scan: No `TBD`, `TODO`, or "implement later" placeholders remain.
- Type consistency: The plan uses existing Docker Compose service names and documented environment variable names.
