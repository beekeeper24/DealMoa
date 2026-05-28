# Auction Activity Ranking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first backend auction activity ranking path so active auctions can be ordered by bid activity, unique bidder count, and ending-soon pressure.

**Architecture:** Keep ranking inside the existing search module because auction ranking is an Elasticsearch read-model concern. PostgreSQL remains source of truth; auction search documents gain `uniqueBidderCount`, and the API exposes a dedicated activity ranking endpoint that uses Elasticsearch script scoring over active auction documents.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Elasticsearch query DSL, pytest.

---

### Task 1: RED Tests For Ranking Inputs And API Shape

**Files:**
- Modify: `apps/api/tests/test_search_documents.py`
- Modify: `apps/api/tests/test_search_indexes.py`
- Modify: `apps/api/tests/test_search_client.py`
- Modify: `apps/api/tests/test_search_api.py`

- [ ] **Step 1: Add document test**

Add a test that creates an `Auction` with three `AuctionBid` rows from two users and expects `build_auction_document()` to include `uniqueBidderCount == 2`.

- [ ] **Step 2: Add mapping test**

Extend the auction mapping assertion so `uniqueBidderCount` is an integer field.

- [ ] **Step 3: Add Elasticsearch ranking test**

Add a MockTransport test that calls `ElasticsearchSearchClient.rank_auctions(limit=1, cursor=None, now=...)` and asserts:
- request path is `/auctions_current/_search`
- query filters `status = active`
- script score includes `bidCount`, `uniqueBidderCount`, and `endsAt`
- sort uses `_score`, `updatedAt`, and `id`

- [ ] **Step 4: Add API route test**

Add a test for `GET /api/v1/search/auctions/activity?limit=1` that verifies the router calls `use_cases.rank_auctions(limit=1, cursor=None)`.

- [ ] **Step 5: Run focused tests and confirm RED**

Run: `PYTHONPATH=apps/api uv run pytest apps/api/tests/test_search_documents.py apps/api/tests/test_search_indexes.py apps/api/tests/test_search_client.py apps/api/tests/test_search_api.py -q`

Expected: FAIL because `uniqueBidderCount`, `rank_auctions`, and the activity route do not exist yet.

### Task 2: Implement Ranking Read Model And Query

**Files:**
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/search/documents.py`
- Modify: `apps/api/app/modules/search/indexes.py`
- Modify: `apps/api/app/modules/search/client.py`
- Modify: `apps/api/app/modules/search/use_cases.py`
- Modify: `apps/api/app/modules/search/router.py`
- Modify: `apps/api/app/modules/search/schemas.py`

- [ ] **Step 1: Load auction bids for rebuild**

Use `selectinload(Auction.bids)` in `ProductRepository.list_auctions_for_search()` so full reindex can compute unique bidders without N+1 queries.

- [ ] **Step 2: Add document and mapping field**

Add `uniqueBidderCount` to auction documents and map it as `integer`.

- [ ] **Step 3: Add search client ranking method**

Add `rank_auctions(limit, cursor, now=None)` to build an Elasticsearch `script_score` query over active auctions. The script should score:
- bid activity from `bidCount` up to 45
- unique bidders from `uniqueBidderCount` up to 20
- ending-soon pressure from `endsAt` up to 5

- [ ] **Step 4: Add use case and API route**

Expose `SearchUseCases.rank_auctions()` and `GET /api/v1/search/auctions/activity`.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run: `PYTHONPATH=apps/api uv run pytest apps/api/tests/test_search_documents.py apps/api/tests/test_search_indexes.py apps/api/tests/test_search_client.py apps/api/tests/test_search_api.py -q`

Expected: PASS.

### Task 3: Docs, Verification, And Integration

**Files:**
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document the activity endpoint**

Add `GET /api/v1/search/auctions/activity` and clarify that this slice implements available signals first: bid activity, unique bidders, ending soon, active filter.

- [ ] **Step 2: Update handoff**

Record the slice as implemented on `feature/auction-activity-ranking` and make outbid notifications the next likely auction slice.

- [ ] **Step 3: Run full verification**

Run backend/consumer/worker pytest, ruff, mypy, compose config, API Docker build, and `git diff --check` before commit/PR.
