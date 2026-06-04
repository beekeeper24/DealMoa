# Admin Crawler Run Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #53 so an admin can enqueue an allowlisted crawler Celery task from the API and admin web UI.

**Architecture:** FastAPI owns authentication, admin authorization, request validation, and queue dispatch. The API depends on a small crawler task queue port and a Celery-backed adapter; it does not import `worker_app.tasks` or accept arbitrary task names/URLs. The web admin crawler run log page posts a trigger request, shows the Celery task id, and refreshes run logs.

**Tech Stack:** FastAPI, Pydantic, Celery client, Redis broker, Next.js, React, TypeScript, Vitest, pytest.

---

## File Structure

- Modify `apps/api/pyproject.toml` and `uv.lock`
  - Add `celery[redis]` to the API package because the API container must enqueue Celery tasks in Railway without relying on worker dependencies.
- Modify `apps/api/app/core/config.py`
  - Add `CELERY_BROKER_URL` for API-side Celery client configuration.
- Create `apps/api/app/modules/crawlers/task_queue.py`
  - Define allowlisted crawler task names and a `CeleryCrawlerTaskQueue` adapter that calls `send_task("dealmoa.<task>")`.
- Modify `apps/api/app/modules/crawlers/schemas.py`
  - Add trigger request/response schemas with camelCase JSON aliases.
- Modify `apps/api/app/modules/crawlers/use_cases.py`
  - Add admin-only trigger use case that calls the task queue port.
- Modify `apps/api/app/modules/crawlers/router.py`
  - Add `POST /api/v1/admin/crawler-runs/trigger`.
- Modify `apps/api/tests/test_crawler_run_logs_api.py`
  - Add fake queue tests for auth, admin authorization, allowed enqueue, and invalid task validation.
- Modify `apps/web/src/admin/types.ts`
  - Add crawler task name and trigger response types.
- Modify `apps/web/src/admin/api.ts`
  - Add `triggerAdminCrawlerRun`.
- Modify `apps/web/src/admin/AdminCrawlerRunLogPage.tsx`
  - Add Mock/Live trigger buttons, loading state, success/error message, and log refresh.
- Modify `apps/web/src/admin/__tests__/api.test.ts`
  - Add API client POST test.
- Modify `apps/web/src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx`
  - Add UI trigger test.
- Modify `docs/async-events.md`, `docs/security-abuse.md`, `docs/submissions.md`, and `docs/handoff.md`
  - Document admin trigger boundaries and non-goals.

## Task 1: API Red Tests

**Files:**
- Modify: `apps/api/tests/test_crawler_run_logs_api.py`

- [x] **Step 1: Write failing API tests**

Add a fake task queue and tests:

```python
class FakeCrawlerTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue(self, task_name: str) -> str:
        self.enqueued.append(task_name)
        return f"celery-{task_name}"
```

Extend `make_test_client` with an optional queue override and add tests for:

```python
def test_admin_crawler_run_trigger_requires_bearer_token() -> None: ...
def test_admin_crawler_run_trigger_requires_admin_role() -> None: ...
def test_admin_can_trigger_allowlisted_crawler_task() -> None: ...
def test_admin_crawler_run_trigger_rejects_unknown_task_name() -> None: ...
```

- [x] **Step 2: Run API red tests**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_crawler_run_logs_api.py -q
```

Expected: tests fail because `get_crawler_task_queue` and `/trigger` do not exist.

## Task 2: API Implementation

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `uv.lock`
- Modify: `apps/api/app/core/config.py`
- Create: `apps/api/app/modules/crawlers/task_queue.py`
- Modify: `apps/api/app/modules/crawlers/schemas.py`
- Modify: `apps/api/app/modules/crawlers/use_cases.py`
- Modify: `apps/api/app/modules/crawlers/router.py`

- [x] **Step 1: Add API Celery dependency**

Run:

```bash
uv add --package dealmoa-api "celery[redis]>=5.5.3"
```

- [x] **Step 2: Add settings, schemas, task queue, use case, and route**

Add:

```python
celery_broker_url: str = Field(
    default="redis://localhost:6379/1",
    validation_alias="CELERY_BROKER_URL",
)
```

Add only these accepted task names:

```python
CrawlerTaskName = Literal["crawl_hot_deals_mock", "crawl_live_urls"]
```

The route should be:

```python
@admin_router.post("/trigger", response_model=CrawlerRunTriggerResponse)
```

- [x] **Step 3: Run API green tests**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_crawler_run_logs_api.py -q
```

Expected: all tests in the file pass.

## Task 3: Web Red Tests

**Files:**
- Modify: `apps/web/src/admin/__tests__/api.test.ts`
- Modify: `apps/web/src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx`

- [x] **Step 1: Write failing web tests**

Add one API client test asserting:

```typescript
expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/crawler-runs/trigger", {
  body: JSON.stringify({ taskName: "crawl_live_urls" }),
  headers: {
    Accept: "application/json",
    Authorization: "Bearer access-1",
    "Content-Type": "application/json"
  },
  method: "POST"
});
```

Add one UI test that clicks `Live 크롤러 실행`, expects `요청됨 celery-1`, and confirms the run log list is fetched again.

- [x] **Step 2: Run web red tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx
```

Expected: tests fail because `triggerAdminCrawlerRun` and buttons do not exist.

## Task 4: Web Implementation

**Files:**
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/api.ts`
- Modify: `apps/web/src/admin/AdminCrawlerRunLogPage.tsx`

- [x] **Step 1: Add types and API client**

Add:

```typescript
export type AdminCrawlerTaskName = "crawl_hot_deals_mock" | "crawl_live_urls";
```

Add `triggerAdminCrawlerRun` that POSTs `{ taskName }` and returns `{ taskName, celeryTaskId }`.

- [x] **Step 2: Add admin buttons and state**

Add two buttons:

- `Mock 크롤러 실행`
- `Live 크롤러 실행`

On success, show `요청됨 <celeryTaskId>` and refresh the first page of logs.

- [x] **Step 3: Run web green tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx
```

Expected: both focused web test files pass.

## Task 5: Docs, Security Review, and Final Verification

**Files:**
- Modify: `docs/async-events.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/submissions.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Document the boundary**

Document that admin trigger:

- accepts only `crawl_hot_deals_mock` and `crawl_live_urls`;
- does not accept arbitrary task names;
- does not accept per-request URLs;
- still relies on worker source profile, parser, SSRF, and rate-limit checks.

- [x] **Step 2: Run focused and full verification**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/api/tests/test_crawler_run_logs_api.py apps/worker/tests/test_tasks.py -q
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts src/admin/__tests__/AdminCrawlerRunLogPage.test.tsx
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
docker compose --profile core --profile worker config --quiet
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
corepack pnpm --filter @dealmoa/web exec playwright test
git diff --check
```

- [x] **Step 3: Run focused security review**

Review the diff for:

- admin auth required before enqueue;
- only allowlisted task names;
- no arbitrary URL or task injection;
- no secrets in docs or config;
- API imports Celery client only, not worker task code.
