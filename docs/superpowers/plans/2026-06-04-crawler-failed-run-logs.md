# Crawler Failed Run Logs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist failed crawler task runs so admins can distinguish "task did not run" from "task ran and failed."

**Architecture:** Extend `crawler_run_logs` with optional failure fields. Worker crawler tasks still rollback any submission writes on failure, then open a separate short transaction to persist a failed run log. Admin API and web expose the failure fields without storing fetched HTML or raw exception payloads.

**Tech Stack:** Python 3.12, SQLAlchemy, Alembic, FastAPI, Celery worker, Next.js, React, TypeScript, Vitest.

---

## Scope

- [x] Add nullable `error_type` and `error_message` to crawler run logs.
- [x] Serialize failure fields through admin crawler run API.
- [x] Record failed `crawl_hot_deals_mock` and `crawl_live_urls` runs after rollback.
- [x] Keep failed logs separate from retry metadata and scheduler control.
- [x] Show failure fields in `/admin/crawler-runs`.
- [x] Update docs/handoff and verify.

## Acceptance Criteria

- Successful crawler run logs still have `status = succeeded` and no failure fields.
- Failed crawler run logs have `status = failed`, `errorType`, and a bounded `errorMessage`.
- Failed crawler logging does not store fetched HTML.
- Failed crawler logging persists even after the task's main DB transaction is rolled back.
- The original exception is re-raised so Celery retry/failure behavior is not hidden.
- Admin crawler run API returns failure fields; non-admin rules are unchanged.
- This slice does not add retry scheduling, manual crawler controls, Redis-backed rate windows, or crawl delay policies.

## Files

- Modify: `apps/api/app/modules/crawlers/models.py`
- Modify: `apps/api/app/modules/crawlers/schemas.py`
- Modify: `apps/api/tests/test_crawler_run_logs_api.py`
- Modify: `apps/api/tests/test_crawler_run_logs_models.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`
- Create: `apps/api/alembic/versions/20260604_0015_crawler_run_log_failures.py`
- Modify: `apps/worker/worker_app/tasks.py`
- Modify: `apps/worker/tests/test_tasks.py`
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/AdminCrawlerRunLogPage.tsx`
- Modify: `apps/web/src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx`
- Modify: `apps/web/src/admin/__tests__/api.test.ts`
- Modify: `docs/async-events.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/submissions.md`
- Modify: `docs/handoff.md`

## Tasks

- [x] Write failing API/model/migration tests for failure fields.
- [x] Write failing worker tests proving failed live crawler runs rollback submissions but persist one failed run log and re-raise.
- [x] Write failing web tests proving failed run logs display `errorType` and `errorMessage`.
- [x] Implement migration, model fields, serializers, and test fixture updates.
- [x] Implement worker failure log helper with separate transaction after rollback.
- [x] Implement web failure field rendering.
- [x] Update docs with completed scope and deferred retry/scheduling controls.
- [x] Run focused tests, full Python tests, web checks, security grep, `git diff --check`.
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
