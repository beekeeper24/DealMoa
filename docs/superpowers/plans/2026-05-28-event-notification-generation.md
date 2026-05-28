# Event Notification Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move new deal/new auction notification fan-out from the synchronous Product API path to a Kafka domain-event consumer.

**Architecture:** The API keeps writing `deal.created` and `auction.created` outbox events in the same transaction as the offer mutation, but stops creating notification rows directly. `apps/consumer` gains a `consume-notifications` command that subscribes to domain events, loads the relevant aggregate, and reuses `NotificationGenerationUseCases` to create deduplicated user notifications.

**Tech Stack:** FastAPI shared modules, SQLAlchemy, aiokafka, Pytest, Ruff, Mypy.

---

## Scope

- Add a notification domain-event handler for `deal.created` and `auction.created`.
- Add `consume-notifications` consumer command and Kafka consumer group setting.
- Remove synchronous notification generation injection from Product API.
- Keep `NotificationGenerationUseCases` as the reusable fan-out implementation.
- Update docs/handoff/env examples.

Out of scope:

- Web notification dropdown.
- Push/email delivery.
- Auction ending-soon scheduled notifications.
- Processed-event idempotency table beyond the existing notification target unique index.

## Tasks

### Task 1: Consumer Notification Handler

- [x] Write failing tests for `DomainEventNotificationGenerator` handling `deal.created`, `auction.created`, unknown events, missing aggregates, and duplicate delivery.
- [x] Implement the handler with `ProductRepository`, `FavoritesRepository`, `NotificationsRepository`, and `NotificationGenerationUseCases`.
- [x] Verify handler tests pass.

### Task 2: Move API Path To Event-Only Notification Generation

- [x] Write/adjust API tests showing deal/auction creation no longer creates notifications synchronously.
- [x] Remove `NotificationGenerationUseCases` from Product API dependency injection and Product use case calls.
- [x] Verify product, domain event, and notification generation tests pass.

### Task 3: Runtime Command And Docs

- [x] Add `KAFKA_NOTIFICATION_GROUP_ID`.
- [x] Add `consume-notifications` command in `apps/consumer`.
- [x] Document local runtime command and update handoff active/completed scope.
- [x] Run backend ruff, mypy, pytest, Docker Compose config, Docker builds, web checks, focused notification/Kafka security grep, and `git diff --check`.
