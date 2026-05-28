# Notification Generation MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate notification rows when favorited products receive new deals or auctions.

**Architecture:** Keep generation as a reusable API-side use case that can later be called by a Kafka consumer. For the MVP, Product API deal/auction creation invokes it synchronously in the same DB transaction. Duplicate prevention uses a unique notification target index plus repository checks.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pytest.

---

## Scope

- Product favorite users receive `new_deal` when a new deal is created for that product.
- Product favorite users receive `new_auction` when a new auction is created for that product.
- Duplicate notification rows for the same `(user, type, targetType, targetId)` are prevented.
- Kafka/Celery runtime remains deferred; only the reusable generation boundary is added.

Out of scope:

- Auction ending-soon scheduled generation.
- Kafka topics/consumer app.
- Celery beat/worker app.
- Web notification popup.

## Tasks

### Task 1: Dedupe Contract

- [x] Add a unique notification target index for `(user_id, type, target_type, target_id)`.
- [x] Update model tests and Alembic migration coverage.

### Task 2: Generation Use Case

- [x] Add favorite repository methods for product favorite user ids.
- [x] Add notification repository lookup for existing target notification.
- [x] Add notification fan-out use case for new deals and new auctions.
- [x] Test user scoping and duplicate prevention.

### Task 3: Product Creation Integration

- [x] Inject notification fan-out into `ProductUseCases`.
- [x] Trigger fan-out after deal/auction creation.
- [x] Test Product API creates notifications for favorited product users.

### Task 4: Docs And Verification

- [x] Update `docs/notifications.md` and `docs/handoff.md`.
- [x] Run API lint/typecheck/tests, Docker Compose config, API Docker build, fan-out security grep, and `git diff --check`.
