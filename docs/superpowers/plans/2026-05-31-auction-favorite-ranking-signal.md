# Auction Favorite Ranking Signal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add auction favorite count as the first `Interest` signal in auction activity ranking.

**Architecture:** Keep favorite count as a denormalized Elasticsearch read-model field. PostgreSQL remains source of truth; `SearchUseCases` asks `ProductRepository` for auction favorite counts during full reindex and single auction upserts, then the activity ranking script adds a capped `favoriteCount` contribution.

**Tech Stack:** Python 3.12, SQLAlchemy, Elasticsearch query DSL, pytest.

---

### Task 1: RED Tests For Favorite Count Ranking

**Files:**
- Modify: `apps/api/tests/test_search_documents.py`
- Modify: `apps/api/tests/test_search_indexes.py`
- Modify: `apps/api/tests/test_search_client.py`
- Modify: `apps/api/tests/test_search_rebuild.py`

- [ ] **Step 1: Add document test**

Assert `build_auction_document(auction, favorite_count=7)` includes `favoriteCount == 7`, while the default remains `0`.

- [ ] **Step 2: Add mapping test**

Assert auction index mapping contains `favoriteCount` as an integer field.

- [ ] **Step 3: Add script test**

Assert `rank_auctions()` script references `favoriteCount` and has `favoriteCountWeight == 10.0`.

- [ ] **Step 4: Add use-case test**

Assert full reindex and single `index_auction()` pass repository-provided favorite counts into auction documents.

- [ ] **Step 5: Run focused tests and confirm RED**

Run: `PYTHONPATH=apps/api uv run pytest apps/api/tests/test_search_documents.py apps/api/tests/test_search_indexes.py apps/api/tests/test_search_client.py apps/api/tests/test_search_rebuild.py -q`

Expected: FAIL because `favoriteCount` is not in documents, mapping, script, or use-case wiring yet.

### Task 2: Implement Favorite Count Signal

**Files:**
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/search/documents.py`
- Modify: `apps/api/app/modules/search/indexes.py`
- Modify: `apps/api/app/modules/search/client.py`
- Modify: `apps/api/app/modules/search/use_cases.py`

- [ ] **Step 1: Add favorite count queries**

Implement `ProductRepository.count_auction_favorites(auction_id)` and `list_auction_favorite_counts()`.

- [ ] **Step 2: Add document and mapping field**

Add `favoriteCount` to auction documents and map it as `integer`.

- [ ] **Step 3: Wire SearchUseCases**

Use bulk counts in `rebuild_indexes()` and per-auction count in `index_auction()`.

- [ ] **Step 4: Add interest score to script**

Add capped `favoriteCount` contribution with max 10 points to `AUCTION_ACTIVITY_SCRIPT`.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run the focused pytest command from Task 1 again.

### Task 3: Docs, Verification, And Integration

**Files:**
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document signal status**

Clarify that `Interest` is now implemented from `favoriteCount`, while view momentum and trust remain later slices.

- [ ] **Step 2: Run full verification**

Run backend/consumer/worker pytest, ruff, mypy, compose config, API Docker build, web lint/test/build, and `git diff --check` before commit/PR.
