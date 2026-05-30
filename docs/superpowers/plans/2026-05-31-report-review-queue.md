# Report Review Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first report intake and admin review queue so reports become review priority signals without directly affecting ranking.

**Architecture:** Store user reports in PostgreSQL as `offer_reports`. User APIs create idempotent open reports for deal/auction targets. Admin APIs list reports and resolve/dismiss them with an audit log entry. No search document, ranking score, or offer status changes happen automatically from report count.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, existing bearer auth, admin role checks, Pydantic schemas, pytest.

---

### Task 1: Report Model And Migration

**Files:**
- Create: `apps/api/app/modules/reports/models.py`
- Create: `apps/api/alembic/versions/20260531_0010_offer_reports.py`
- Modify: `apps/api/alembic/env.py`
- Test: `apps/api/tests/test_reports_models.py`
- Test: `apps/api/tests/test_alembic_migrations.py`

- [x] Add failing model tests for `offer_reports` columns, user FK, and lookup indexes.
- [x] Add failing Alembic expectation for `offer_reports`.
- [x] Implement `OfferReport` with `user_id`, `target_type`, `target_id`, `reason_code`, `description`, `status`, reviewer/resolution fields, and timestamps.

### Task 2: Report Use Cases

**Files:**
- Create: `apps/api/app/modules/reports/repository.py`
- Create: `apps/api/app/modules/reports/schemas.py`
- Create: `apps/api/app/modules/reports/use_cases.py`
- Modify: `apps/api/app/core/exceptions.py`
- Test: `apps/api/tests/test_reports_use_cases.py`

- [x] Add failing tests for authenticated user report creation on deals and auctions.
- [x] Add failing tests that duplicate open report returns the existing open report.
- [x] Add failing tests for missing target -> existing not-found exceptions.
- [x] Add failing tests for admin report list pagination.
- [x] Add failing tests for non-admin forbidden and admin resolve/dismiss with audit log.

### Task 3: Report APIs

**Files:**
- Create: `apps/api/app/modules/reports/router.py`
- Modify: `apps/api/app/api/v1/router.py`
- Test: `apps/api/tests/test_reports_api.py`

- [x] Add failing API tests for auth-required report create routes.
- [x] Add failing API tests for `POST /api/v1/reports/deals/{deal_id}` and `POST /api/v1/reports/auctions/{auction_id}`.
- [x] Add failing API tests for admin-only `GET /api/v1/admin/reports`.
- [x] Add failing API tests for admin-only `PATCH /api/v1/admin/reports/{report_id}`.

### Task 4: Docs, Security Review, Verification

**Files:**
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`
- Create: `docs/reports.md`

- [x] Document that report count only prioritizes admin review and does not hide/down-rank content.
- [x] Run a focused security review for auth/admin role enforcement and report payload exposure.
- [ ] Run focused report tests, full backend pytest, ruff, mypy, and web checks if touched.
- [ ] Commit, push, open PR to `develop`, wait for CI, squash merge, sync local `develop`, and write Notion log.
