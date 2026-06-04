# AI Review Rate Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #60 so user-triggered AI first-pass review calls are bounded by a configurable per-user time-window limit.

**Architecture:** Store AI review usage events in PostgreSQL so the API limit works across process restarts and multiple API instances. The limiter is injected into submission and verified-review use cases only from API routers, so internal worker flows that construct the use cases directly are not accidentally blocked. Existing AI review output remains advisory evidence and never publishes content.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic settings, pytest, ruff, mypy.

---

## File Structure

- Create `apps/api/app/modules/ai_review/models.py`
  - SQLAlchemy model for `ai_review_usage_events`.
- Create `apps/api/app/modules/ai_review/rate_limits.py`
  - Repository plus small limiter service for counting and recording usage events.
- Create `apps/api/alembic/versions/20260604_0017_ai_review_usage_events.py`
  - Migration for the usage table and indexes.
- Modify `apps/api/alembic/env.py`
  - Import AI review models for metadata.
- Modify `apps/api/app/core/config.py`
  - Add `AI_REVIEW_USER_WINDOW_LIMIT` and `AI_REVIEW_USER_WINDOW_HOURS`.
- Modify `apps/api/app/core/exceptions.py`
  - Add `AI_REVIEW_RATE_LIMIT_EXCEEDED` with HTTP 429.
- Modify `apps/api/app/modules/submissions/use_cases.py`
  - Check and record usage before a new submission AI review; duplicate source URLs still return existing rows first.
- Modify `apps/api/app/modules/submissions/router.py`
  - Inject the limiter using the current DB session and settings.
- Modify `apps/api/app/modules/evidence/use_cases.py`
  - Check and record usage before verified-review AI review after product existence is confirmed.
- Modify `apps/api/app/modules/evidence/router.py`
  - Inject the same limiter.
- Modify `apps/api/tests/test_submissions_use_cases.py`
  - Add unit tests for limit pass, limit exceeded, and duplicate submission no-charge behavior.
- Modify `apps/api/tests/test_evidence_api.py` or `apps/api/tests/test_evidence_use_cases.py`
  - Add verified-review limit behavior coverage.
- Modify `apps/api/tests/test_alembic_migrations.py`
  - Assert usage table and indexes exist.
- Modify `apps/api/tests/test_config.py`
  - Assert env settings parse.
- Modify `docs/submissions.md`, `docs/price-reviews.md`, `docs/security-abuse.md`, and `docs/handoff.md`
  - Document the cost/abuse boundary and remaining deferred Redis/distributed policy details if any.

## Task 1: RED Tests

- [x] **Step 1: Add settings and migration assertions**

Add tests that expect:

- `AI_REVIEW_USER_WINDOW_LIMIT` parses into settings;
- `AI_REVIEW_USER_WINDOW_HOURS` parses into settings;
- `ai_review_usage_events` table exists;
- table indexes include user/time lookup coverage.

- [x] **Step 2: Add submission limiter tests**

Add tests that expect:

- first new submission under the limit calls the AI provider and records usage;
- second new submission over a test limit of `1` raises `AI_REVIEW_RATE_LIMIT_EXCEEDED`;
- duplicate `sourceUrl` returns the existing submission and does not call the limiter/provider again.

- [x] **Step 3: Add verified-review limiter test**

Add a test that creates one verified review under a test limit of `1`, then rejects the second verified review for the same user with `AI_REVIEW_RATE_LIMIT_EXCEEDED`.

- [x] **Step 4: Run RED command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_submissions_use_cases.py apps/api/tests/test_evidence_api.py apps/api/tests/test_config.py apps/api/tests/test_alembic_migrations.py -q
```

Expected: fail because the limiter, settings, migration, and error code do not exist.

## Task 2: Implementation

- [x] **Step 1: Add DB model and migration**

Create `AIReviewUsageEvent` with:

- `id`;
- `user_id`;
- `target_type` (`submission` or `verified_review`);
- `created_at`.

Add indexes for:

- `(user_id, created_at)`;
- `(user_id, target_type, created_at)`.

- [x] **Step 2: Add limiter service**

Implement:

```python
class AIReviewRateLimiter:
    def check_and_record(self, *, user_id: str, target_type: str, now: datetime) -> None:
        ...
```

Behavior:

- if `window_limit <= 0`, do nothing;
- count usage events for the user since `now - window_hours`;
- if count is at or above the limit, raise `AIReviewRateLimitExceededException`;
- otherwise insert one usage event.

- [x] **Step 3: Wire limiter into submissions**

For new submissions only:

1. check duplicate source URL first;
2. call `check_and_record`;
3. call the AI provider;
4. create the pending submission.

- [x] **Step 4: Wire limiter into verified reviews**

For verified reviews:

1. confirm product exists first;
2. call `check_and_record`;
3. call the AI provider;
4. create the pending review.

- [x] **Step 5: Run GREEN command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_submissions_use_cases.py apps/api/tests/test_evidence_api.py apps/api/tests/test_config.py apps/api/tests/test_alembic_migrations.py -q
```

Expected: selected tests pass.

## Task 3: Docs, Security Review, and Verification

- [x] **Step 1: Update docs**

Document:

- the limiter protects user-triggered AI first-pass review calls;
- it does not publish or approve content;
- duplicate submission URLs do not consume new quota;
- default limit and env variable names;
- Redis or provider-side quota monitoring can still be added later if needed.

- [x] **Step 2: Focused security review**

Review the diff for:

- no automatic publishing/approval;
- no proof reference sent to OpenAI;
- no secret logging;
- 429 uses a stable error code;
- worker/crawler flows are not accidentally blocked.

- [x] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
git diff --check
```

- [ ] **Step 4: Commit and integrate**

Commit the verified slice, push `feature/ai-review-rate-limits`, open a PR into `develop`, wait for CI, merge if green, sync local `develop`, and write a Notion work log.

## Self-Review

- Spec coverage: Issue #60 acceptance criteria map to Task 1 tests, Task 2 implementation, and Task 3 docs/security checks.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: limiter uses `target_type` as a string boundary to avoid leaking schema literals across modules; tests will lock allowed values.
