# Auction Bid Search Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `auction.bid.placed` Kafka domain events refresh the auction search document with the latest persisted price and bid count.

**Architecture:** The consumer search indexer treats bid placement as an auction aggregate update. It reads the canonical `Auction` row by `aggregateId` and rebuilds the Elasticsearch document from database state rather than trusting event payload values.

**Tech Stack:** Python 3.12, pytest, SQLAlchemy, FastAPI shared domain modules, consumer search indexer.

---

### Task 1: Add Failing Consumer Test

**Files:**
- Modify: `apps/consumer/tests/test_domain_event_search_indexer.py`

- [ ] **Step 1: Write the failing test**

Add `test_handle_auction_bid_placed_refreshes_auction_document` that seeds an auction at the post-bid state, handles `auction.bid.placed`, and expects one `auctions` document with `currentPrice` and `bidCount` from the database row.

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=apps/api:apps/consumer uv run pytest apps/consumer/tests/test_domain_event_search_indexer.py -q`

Expected: FAIL because `DomainEventSearchIndexer.handle()` currently returns `False` for `auction.bid.placed`.

### Task 2: Implement Event Handling

**Files:**
- Modify: `apps/consumer/consumer_app/domain_events.py`

- [ ] **Step 1: Add the event type**

Extend `DomainEventType` with `"auction.bid.placed"`.

- [ ] **Step 2: Index the auction aggregate**

Handle `"auction.bid.placed"` with the same DB-backed `index_auction()` path as `"auction.created"`.

- [ ] **Step 3: Run focused tests**

Run: `PYTHONPATH=apps/api:apps/consumer uv run pytest apps/consumer/tests/test_domain_event_search_indexer.py -q`

Expected: PASS.

### Task 3: Update Docs And Verify

**Files:**
- Modify: `docs/async-events.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document the new consumer behavior**

Update async event docs so `auction.bid.placed` is no longer described as ignored by the search consumer.

- [ ] **Step 2: Update handoff status**

Record this slice as the current/next coherent PR unit and clarify that search freshness is now covered while ranking/notification follow-ups remain separate.

- [ ] **Step 3: Run full verification**

Run backend/consumer/worker tests, ruff, mypy, docker compose config, consumer image build, diff whitespace check, and a focused Kafka-event security grep before commit/PR.
