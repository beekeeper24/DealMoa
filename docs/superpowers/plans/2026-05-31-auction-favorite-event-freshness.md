# Auction Favorite Event Freshness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep auction `favoriteCount` search documents fresh after auction favorite create/delete without waiting for full reindex.

**Architecture:** Auction favorite mutations write transactional outbox events in the API transaction. The search-index consumer handles those events by reloading the auction from PostgreSQL and upserting the existing auction search document, which already computes current `favoriteCount` from source data.

**Tech Stack:** Python 3.12, FastAPI shared domain modules, SQLAlchemy, Kafka consumer boundary, pytest.

---

### Task 1: RED Tests For Favorite Events And Consumer Freshness

**Files:**
- Modify: `apps/api/tests/test_favorites_use_cases.py`
- Modify: `apps/api/tests/test_domain_events_use_cases.py`
- Modify: `apps/consumer/tests/test_domain_event_search_indexer.py`

- [ ] **Step 1: Add outbox tests**

Add tests that `add_auction_favorite()` records `auction.favorite.created` once for a newly created favorite, and `remove_auction_favorite()` records `auction.favorite.deleted` only when an existing favorite is removed.

- [ ] **Step 2: Add domain event tests**

Add direct tests for `DomainEventsUseCases.record_auction_favorite_created()` and `record_auction_favorite_deleted()` payload shape.

- [ ] **Step 3: Add search consumer test**

Add a consumer test where `auction.favorite.created` and `auction.favorite.deleted` both refresh the auction document and preserve current `favoriteCount`.

- [ ] **Step 4: Run focused tests and confirm RED**

Run: `PYTHONPATH=apps/api:apps/consumer uv run pytest apps/api/tests/test_favorites_use_cases.py apps/api/tests/test_domain_events_use_cases.py apps/consumer/tests/test_domain_event_search_indexer.py -q`

Expected: FAIL because favorite event recording and consumer handling do not exist yet.

### Task 2: Implement Event Freshness

**Files:**
- Modify: `apps/api/app/modules/events/use_cases.py`
- Modify: `apps/api/app/modules/favorites/use_cases.py`
- Modify: `apps/api/app/modules/favorites/router.py`
- Modify: `apps/consumer/consumer_app/domain_events.py`

- [ ] **Step 1: Add domain event methods**

Add `auction.favorite.created` and `auction.favorite.deleted` recorders with auction/user/favorite payloads.

- [ ] **Step 2: Inject events into FavoritesUseCases**

Allow `FavoritesUseCases` to accept optional `DomainEventsUseCases`, and wire it in the router from the same DB session.

- [ ] **Step 3: Record only real mutations**

Record created only when a new favorite row is inserted, and deleted only when a row existed and was removed.

- [ ] **Step 4: Handle search events**

Teach `DomainEventSearchIndexer` to treat `auction.favorite.created/deleted` like an auction aggregate refresh.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run the focused pytest command from Task 1 again.

### Task 3: Docs, Verification, And Integration

**Files:**
- Modify: `docs/async-events.md`
- Modify: `docs/favorites.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document event freshness**

Document that auction favorite create/delete events refresh auction search documents and `favoriteCount`.

- [ ] **Step 2: Run full verification**

Run backend/consumer/worker pytest, ruff, mypy, compose config, consumer Docker build, `git diff --check`, and focused Kafka event security grep before commit/PR.
