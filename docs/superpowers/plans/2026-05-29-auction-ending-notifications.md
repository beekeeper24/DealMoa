# Auction Ending Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate `auction_ending_soon` notifications for users who favorited auctions that are close to ending.

**Architecture:** Keep Kafka for domain events and use Celery for scheduled notification jobs. The API notification module owns the query/generation logic, and `apps/worker` calls it from a registered Celery task plus beat schedule.

**Tech Stack:** FastAPI shared modules, SQLAlchemy, Celery, Redis, Pytest, Ruff, Mypy.

---

## Scope

- Add auction-favorite fan-out for `auction_ending_soon`.
- Add active auction ending-window query.
- Add worker task and Celery beat schedule.
- Add Docker Compose/env/docs/handoff updates.

Out of scope:

- Email/push delivery.
- Web notification dropdown.
- Bid events or auction status transitions.

## Tasks

### Task 1: Notification Domain Logic

**Files:**
- Modify: `apps/api/app/modules/favorites/repository.py`
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/notifications/generation.py`
- Test: `apps/api/tests/test_auction_ending_notifications.py`

- [x] Write failing tests for auction favorite fan-out, active ending-window filtering, and idempotent duplicate runs.
- [x] Add `FavoritesRepository.list_auction_favorite_user_ids`.
- [x] Add `ProductRepository.list_active_auctions_ending_between`.
- [x] Add `NotificationGenerationUseCases.notify_auction_ending_soon`.
- [x] Add `ScheduledNotificationUseCases.generate_auction_ending_soon_notifications`.
- [x] Verify focused API tests pass.

### Task 2: Worker Runtime

**Files:**
- Modify: `apps/worker/worker_app/config.py`
- Modify: `apps/worker/worker_app/celery_app.py`
- Modify: `apps/worker/worker_app/tasks.py`
- Modify: `apps/worker/tests/test_tasks.py`
- Modify: `apps/worker/Dockerfile`
- Modify: `apps/worker/pyproject.toml`

- [x] Write failing worker tests for task registration and database-backed summary payload.
- [x] Add worker `DATABASE_URL`, lookahead, batch size, and schedule settings.
- [x] Register `dealmoa.generate_auction_ending_soon_notifications`.
- [x] Configure Celery beat schedule for the task.
- [x] Copy `apps/api/app` into the worker image and set worker `PYTHONPATH` to include shared API modules.
- [x] Verify focused worker tests pass.

### Task 3: Runtime Docs And Integration

**Files:**
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `docs/async-events.md`
- Modify: `docs/notifications.md`
- Modify: `docs/handoff.md`

- [x] Add worker env vars and a `worker-beat` compose service.
- [x] Document local worker and beat commands.
- [x] Update handoff active/completed scope.
- [x] Run backend ruff, mypy, pytest, Docker Compose config, Docker builds, focused security grep, and `git diff --check`.
