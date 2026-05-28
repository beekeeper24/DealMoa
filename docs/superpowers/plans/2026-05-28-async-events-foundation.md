# Async Events Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real Kafka/Celery code boundary by writing domain events to a transactional outbox, publishing them from `apps/consumer`, and exposing initial Celery task entry points from `apps/worker`.

**Architecture:** FastAPI remains responsible for DB transactions and writes domain events to an outbox table in the same transaction as product/deal/auction mutations. `apps/consumer` polls unpublished outbox rows and publishes them to Kafka with an idempotent event id, while `apps/worker` owns Celery task definitions for background jobs. This slice wires code and runtime scaffolding, but does not move search indexing or notification generation off the synchronous API path yet.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, aiokafka, Celery, Redis, Docker Compose, Pytest, Ruff, Mypy.

---

## Scope

- Create an API-owned `domain_events` outbox table.
- Emit `product.updated`, `deal.created`, and `auction.created` events from Product use cases.
- Add `apps/consumer` with a poll-and-publish use case and Kafka producer adapter.
- Add `apps/worker` with Celery app and initial mock task names.
- Add Docker Compose `event` and `worker` profiles for Kafka, consumer, and worker.
- Update `.env.example`, CI, and docs/handoff.

Out of scope:

- Moving Elasticsearch indexing to Kafka consumers.
- Moving notification generation to Kafka consumers.
- Production Kafka/Railway deployment tuning.
- Real crawler, real AI review, or real embedding jobs.

## Files

- Create `apps/api/app/modules/events/models.py`: SQLAlchemy `DomainEvent` outbox model.
- Create `apps/api/app/modules/events/repository.py`: create/list/mark-published operations.
- Create `apps/api/app/modules/events/use_cases.py`: event payload builders for Product/Deal/Auction.
- Create `apps/api/alembic/versions/20260528_0006_domain_events_outbox.py`: outbox migration.
- Modify `apps/api/alembic/env.py`: import events models for migrations.
- Modify `apps/api/app/modules/products/router.py`: inject `DomainEventsUseCases`.
- Modify `apps/api/app/modules/products/use_cases.py`: emit events after successful create/update paths.
- Create `apps/api/tests/test_domain_events_models.py`: model contract.
- Create `apps/api/tests/test_domain_events_use_cases.py`: payload and outbox write tests.
- Create `apps/api/tests/test_product_domain_events.py`: Product API integration tests for outbox rows.
- Create `apps/consumer/pyproject.toml`: consumer dependencies and pytest path.
- Create `apps/consumer/app/config.py`: Kafka/DB settings.
- Create `apps/consumer/app/outbox_publisher.py`: polling publisher use case.
- Create `apps/consumer/app/kafka.py`: aiokafka adapter.
- Create `apps/consumer/app/main.py`: CLI loop entrypoint.
- Create `apps/consumer/tests/test_outbox_publisher.py`: fake producer tests.
- Create `apps/consumer/Dockerfile`: Railway/Docker runnable image.
- Create `apps/worker/pyproject.toml`: worker dependencies.
- Create `apps/worker/app/celery_app.py`: Celery app configuration.
- Create `apps/worker/app/tasks.py`: initial mock task functions.
- Create `apps/worker/tests/test_tasks.py`: task registration and return shape tests.
- Create `apps/worker/Dockerfile`: Railway/Docker runnable image.
- Modify `pyproject.toml`: include `apps/consumer` and `apps/worker` in uv workspace.
- Modify `docker-compose.yml`: add Kafka, consumer, worker profiles.
- Modify `.env.example`: add Kafka/Celery variables.
- Modify `.github/workflows/ci.yml`: lint/typecheck/test consumer and worker.
- Create `docs/async-events.md`: outbox/Kafka/Celery boundary docs.
- Modify `docs/architecture.md`, `docs/handoff.md`: mark active/completed scope.

## Tasks

### Task 1: Transactional Outbox Contract

- [x] Write failing model and migration tests for `domain_events`.
- [x] Run `uv run pytest apps/api/tests/test_domain_events_models.py apps/api/tests/test_alembic_migrations.py -q` and verify failure from missing model/table.
- [x] Add `DomainEvent` model with `event_type`, `aggregate_type`, `aggregate_id`, `payload_json`, `published_at`, `created_at`, `updated_at`.
- [x] Add Alembic migration `20260528_0006_domain_events_outbox`.
- [x] Import events models in Alembic env.
- [x] Run the same tests and verify pass.

### Task 2: API Event Emission

- [x] Write failing tests proving Product create emits `product.updated`, Deal create emits `deal.created`, and Auction create emits `auction.created`.
- [x] Add repository and use-case helpers for domain event creation.
- [x] Inject event use case into Product API dependencies.
- [x] Emit events after the Product/Deal/Auction row has an id and before transaction commit.
- [x] Run focused Product/event tests and verify pass.

### Task 3: Consumer Publisher

- [x] Write failing consumer tests for polling unpublished events, publishing to a fake producer, and marking rows as published.
- [x] Add `apps/consumer` package with settings, Kafka adapter, outbox publisher, and CLI entrypoint.
- [x] Run consumer tests and verify pass.

### Task 4: Worker Tasks

- [x] Write failing worker tests for Celery app configuration and initial task names.
- [x] Add `apps/worker` package with Celery app and mock tasks: `crawl_hot_deals_mock`, `ai_review_submission_mock`, `rebuild_search_index`.
- [x] Run worker tests and verify pass.

### Task 5: Runtime, CI, Docs

- [x] Add Dockerfiles for consumer and worker.
- [x] Add Docker Compose `event` and `worker` profiles.
- [x] Add env examples for Kafka topic, consumer poll interval, Celery broker/backend.
- [x] Update CI to lint/typecheck/test `apps/api`, `apps/consumer`, and `apps/worker`.
- [x] Update docs and handoff.
- [x] Run full local verification: ruff, mypy, pytest, compose config, Docker builds, focused Kafka/Celery grep, and `git diff --check`.
