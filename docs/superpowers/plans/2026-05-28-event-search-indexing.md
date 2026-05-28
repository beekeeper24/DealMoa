# Event Search Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consume domain events and update the matching Elasticsearch search document for Product, Deal, and Auction changes.

**Architecture:** Keep API-side full reindex unchanged, then add a single-document indexing method to the existing search client. `apps/consumer` gains a domain-event handler that loads the aggregate from PostgreSQL, builds the existing search document, and indexes it. Kafka subscription is introduced as a second consumer runtime command so outbox publishing and event side effects stay separate but share configuration.

**Tech Stack:** FastAPI shared modules, SQLAlchemy, Elasticsearch HTTP client, aiokafka, Pytest, Ruff, Mypy.

---

## Scope

- Add `index_document(kind, document)` to the search client contract.
- Handle `product.updated`, `deal.created`, and `auction.created` domain event envelopes.
- Add a Kafka subscriber adapter that consumes JSON domain-event messages and dispatches them to the handler.
- Keep the existing admin full reindex endpoint unchanged.
- Keep notification generation synchronous for now.

Out of scope:

- Deleting search documents.
- Retrying/dead-letter queues.
- Idempotent processed-event table.
- Moving notification generation to consumer.
- Running both publisher and subscriber in a single production process.

## Files

- Modify `apps/api/app/modules/search/client.py`: add single-document index API.
- Modify `apps/api/app/modules/search/use_cases.py`: extend `SearchClient` protocol and add `index_product`, `index_deal`, `index_auction`.
- Modify `apps/api/tests/test_search_client.py`: cover single-document Elasticsearch request.
- Modify `apps/api/tests/test_search_rebuild.py`: cover single-document use cases.
- Modify `apps/consumer/consumer_app/config.py`: add subscriber mode settings.
- Create `apps/consumer/consumer_app/domain_events.py`: event envelope validation and search indexing handler.
- Modify `apps/consumer/consumer_app/kafka.py`: add JSON domain-event subscriber adapter.
- Modify `apps/consumer/consumer_app/main.py`: support `publish-outbox` and `consume-search-index` commands.
- Create `apps/consumer/tests/test_domain_event_search_indexer.py`: handler tests.
- Create `apps/consumer/tests/test_kafka_subscriber.py`: subscriber dispatch tests with fake messages.
- Modify `.env.example`, `docker-compose.yml`, `docs/async-events.md`, `docs/search-ranking.md`, `docs/handoff.md`.

## Tasks

### Task 1: Search Client Single-Document Indexing

- [x] Write failing tests for `ElasticsearchSearchClient.index_document`.
- [x] Add `index_document(kind, document)` to the concrete client.
- [x] Extend `SearchClient` protocol and `SearchUseCases` with `index_product`, `index_deal`, and `index_auction`.
- [x] Run focused search client/use-case tests and verify pass.

### Task 2: Domain Event Search Handler

- [x] Write failing tests for `DomainEventSearchIndexer` handling `product.updated`, `deal.created`, and `auction.created`.
- [x] Implement event envelope parsing with allowlisted event types only.
- [x] Load aggregate rows with `ProductRepository` and call the matching search use case.
- [x] Treat missing aggregates as no-op so replaying stale events does not crash the consumer loop.
- [x] Run handler tests and verify pass.

### Task 3: Kafka Subscriber Runtime

- [x] Write failing tests for JSON subscriber dispatch and invalid JSON rejection.
- [x] Add subscriber adapter using `AIOKafkaConsumer`.
- [x] Add `consume-search-index` command while keeping `publish-outbox` as the default command.
- [x] Wire Docker Compose consumer command explicitly to `publish-outbox` and document the search index subscriber command.
- [x] Run consumer tests and verify pass.

### Task 4: Docs And Verification

- [x] Update env examples and docs for search indexing consumer.
- [x] Update handoff active scope.
- [x] Run backend ruff, mypy, pytest, compose config, API/consumer/worker Docker builds, web checks, focused Kafka security grep, and `git diff --check`.
