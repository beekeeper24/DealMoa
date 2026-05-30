# Admin Offer Status Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first admin-only offer status review API so status changes can gate search visibility and ranking trust through the existing read model.

**Architecture:** Keep report counts out of automatic ranking. Admin users change Deal/Auction status through `/api/v1/admin/...` endpoints; the API writes an immutable admin audit log row and a transactional outbox event. The search consumer handles those status-change events by rebuilding the current deal/auction Elasticsearch document from PostgreSQL.

**Tech Stack:** FastAPI dependencies, SQLAlchemy/Alembic, existing AuthUseCases bearer auth, transactional outbox, Kafka consumer search indexer, pytest.

---

### Task 1: Admin Audit Model And Migration

**Files:**
- Create: `apps/api/app/modules/admin/models.py`
- Create: `apps/api/alembic/versions/20260531_0009_admin_audit_logs.py`
- Modify: `apps/api/alembic/env.py`
- Test: `apps/api/tests/test_admin_models.py`
- Test: `apps/api/tests/test_alembic_migrations.py`

- [x] Add failing model tests for `admin_audit_logs` columns, foreign key to `users`, and target/action indexes.
- [x] Add failing Alembic test expectation for `admin_audit_logs`.
- [x] Implement `AdminAuditLog` with `actor_user_id`, `action`, `target_type`, `target_id`, `previous_status`, `new_status`, `reason`, timestamps.
- [x] Add Alembic migration and import admin models in env.py.

### Task 2: Admin Authorization And Offer Status Use Cases

**Files:**
- Create: `apps/api/app/modules/admin/repository.py`
- Create: `apps/api/app/modules/admin/use_cases.py`
- Modify: `apps/api/app/core/exceptions.py`
- Modify: `apps/api/app/modules/events/use_cases.py`
- Test: `apps/api/tests/test_admin_use_cases.py`

- [x] Add failing tests that non-admin users receive `FORBIDDEN` from use cases.
- [x] Add failing tests that admin can change deal and auction status, writes audit log, and records `deal.status.changed` / `auction.status.changed`.
- [x] Add failing test that unsupported status is rejected with common validation error or 422 at API boundary.
- [x] Implement `ForbiddenException`, repository status update helpers, audit log creation, and domain event recording.

### Task 3: Admin API Routes

**Files:**
- Create: `apps/api/app/modules/admin/router.py`
- Modify: `apps/api/app/api/v1/router.py`
- Test: `apps/api/tests/test_admin_api.py`

- [x] Add failing API tests for missing bearer token -> 401, USER role -> 403, ADMIN role -> 200.
- [x] Add failing API tests that response includes updated status and audit reason is persisted.
- [x] Implement `/api/v1/admin/deals/{deal_id}/status` and `/api/v1/admin/auctions/{auction_id}/status`.

### Task 4: Search Consumer Freshness

**Files:**
- Modify: `apps/consumer/consumer_app/domain_events.py`
- Modify: `apps/consumer/tests/test_domain_event_search_indexer.py`

- [x] Add failing consumer tests that `deal.status.changed` refreshes deal document and `auction.status.changed` refreshes auction document with new `trustScore`.
- [x] Handle the new events by reloading canonical PostgreSQL rows and indexing current documents.

### Task 5: Docs, Security Review, Verification

**Files:**
- Modify: `docs/security-abuse.md`
- Modify: `docs/async-events.md`
- Modify: `docs/handoff.md`

- [x] Document that status changes, not report counts, affect visibility and trust.
- [x] Run focused security review for admin role enforcement and audit logging.
- [ ] Run focused tests, full backend pytest, ruff, mypy, and web checks if touched.
- [ ] Commit, push, open PR to `develop`, wait for CI, squash merge, sync local `develop`, and write Notion log.
