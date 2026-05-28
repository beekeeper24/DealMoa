# Notifications MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the authenticated notification data/API baseline before event fan-out and web notification UI.

**Architecture:** Notifications are user-scoped PostgreSQL rows owned by the API module. This slice provides storage, listing, unread counting, and read transitions only. Kafka/Celery producers, favorite-triggered fan-out, web popup UI, and push/email delivery are deferred.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, Pytest.

---

## Scope

- `notifications` SQLAlchemy model and Alembic migration.
- Notification types: `new_deal`, `new_auction`, `auction_ending_soon`.
- User-scoped list API with cursor pagination.
- Unread count API.
- Read-one and read-all APIs.
- Domain/use-case tests and API tests.
- `docs/notifications.md` and handoff updates.

Out of scope:

- Kafka/Celery fan-out.
- Favorite-triggered automatic notification generation.
- Web notification dropdown.
- Email/push delivery.

## API Contract

```http
GET /api/v1/notifications?limit=20&cursor=&unreadOnly=false
GET /api/v1/notifications/unread-count
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/read-all
```

All routes require `Authorization: Bearer <access-token>`.

## Tasks

### Task 1: Notification Persistence

- [x] Write model tests for table columns, user FK, indexes, and type constants.
- [x] Add notification SQLAlchemy model and Alembic migration.
- [x] Update Alembic smoke test to assert the `notifications` table.

### Task 2: Notification Use Cases

- [x] Write use-case tests for user-scoped listing, unread-only filtering, unread count, read-one, read-all, missing notification, and cross-user isolation.
- [x] Implement repository and use-case methods.

### Task 3: Notification API

- [x] Write API tests for auth-required behavior, list, unread count, read-one, and read-all.
- [x] Implement schemas and router.
- [x] Include the router from the API v1 router.

### Task 4: Docs And Verification

- [x] Add `docs/notifications.md`.
- [x] Update `docs/handoff.md`.
- [x] Run API lint/typecheck/tests, Docker Compose config, API Docker build, deployment/security grep, and `git diff --check`.
