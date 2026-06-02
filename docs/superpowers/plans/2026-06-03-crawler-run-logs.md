# Crawler Run Logs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist crawler task run summaries and expose them to admins in a minimal web queue.

**Architecture:** Add a `crawler_run_logs` table owned by the API domain models so both `apps/api` and `apps/worker` can reuse the same SQLAlchemy metadata. Worker tasks create one log row per completed crawler run. Admin API lists logs newest-first, and the web admin page renders the list with pagination.

**Tech Stack:** Python 3.12, SQLAlchemy, Alembic, FastAPI, Celery worker, Next.js, React, TypeScript, Vitest, Playwright.

---

## Scope

- [x] Add `CrawlerRunLog` model, repository, migration, and serializer.
- [x] Record `crawl_hot_deals_mock` and `crawl_live_urls` summaries after successful runs.
- [x] Add admin-only `GET /api/v1/admin/crawler-runs` with cursor pagination.
- [x] Add `apps/web` admin crawler run log page and API client coverage.
- [x] Update crawler docs and handoff.
- [ ] Verify backend, worker, web, CI, PR, merge, and Notion work log.

## Acceptance Criteria

- Admin users can list crawler run logs newest-first.
- Non-admin users receive `FORBIDDEN`; missing bearer token receives `UNAUTHORIZED`.
- Each successful mock/live crawler run writes one log row with task name, status, scanned/fetched/accepted/created/duplicates/skipped counts, skip reasons, and timestamps.
- Empty live crawler runs also write a log row so admins can see that the scheduler ran but had no configured URLs.
- Failed crawler runs are not logged in this slice; failure logging and retry metadata remain deferred.
- This slice does not add production scheduling, Redis-backed distributed rate windows, crawl delay policies, or crawler control buttons.

## Files

- Create: `apps/api/app/modules/crawlers/models.py`
- Create: `apps/api/app/modules/crawlers/repository.py`
- Create: `apps/api/app/modules/crawlers/schemas.py`
- Create: `apps/api/app/modules/crawlers/use_cases.py`
- Create: `apps/api/app/modules/crawlers/router.py`
- Create: `apps/api/app/modules/crawlers/__init__.py`
- Create: `apps/api/alembic/versions/20260603_0014_crawler_run_logs.py`
- Create: `apps/api/tests/test_crawler_run_logs_api.py`
- Create: `apps/api/tests/test_crawler_run_logs_models.py`
- Modify: `apps/api/alembic/env.py`
- Modify: `apps/api/app/api/v1/router.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`
- Modify: `apps/worker/worker_app/tasks.py`
- Modify: `apps/worker/tests/test_tasks.py`
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/api.ts`
- Create: `apps/web/src/admin/AdminCrawlerRunLogPage.tsx`
- Create: `apps/web/src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx`
- Modify: `apps/web/src/admin/__tests__/api.test.ts`
- Create: `apps/web/app/admin/crawler-runs/page.tsx`
- Modify: `apps/web/src/admin/AdminReportQueue.tsx`
- Modify: `apps/web/src/submissions/AdminSubmissionQueue.tsx`
- Modify: `docs/async-events.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/submissions.md`
- Modify: `docs/handoff.md`

## Tasks

- [x] Write failing API/model tests for crawler run log creation, admin listing, auth, and Alembic table/index creation.
- [x] Implement `CrawlerRunLog` SQLAlchemy model, migration, repository, use case, schemas, and router.
- [x] Wire crawler admin router into `api_router` and Alembic metadata imports.
- [x] Write failing worker tests proving mock/live/empty live crawler runs create log rows.
- [x] Implement worker log writes after successful crawler summaries.
- [x] Write failing web API/client and page tests.
- [x] Implement web API client, admin crawler run page, route, and admin navigation link.
- [x] Update docs and run focused/full verification.
- [ ] Commit, push, PR to `develop`, wait for CI, merge, sync local `develop`, and write Notion log.

## Verification Commands

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/api/tests/test_crawler_run_logs_models.py apps/api/tests/test_crawler_run_logs_api.py apps/api/tests/test_alembic_migrations.py apps/worker/tests/test_tasks.py -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
corepack pnpm --filter @dealmoa/web exec playwright test
git diff --check
```
