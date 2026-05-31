# Hot Deal Ranking Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a dedicated hot-deal ranking endpoint that orders active deals by the documented HotDealScore.

**Architecture:** Extend the existing Elasticsearch deal read model with `favoriteCount`, then add a `rank_deals()` search-client method and `/api/v1/search/deals/hot` route. Keep general deal search text-relevance-first. This slice uses full reindex and existing deal upsert paths for `favoriteCount`; deal favorite event freshness remains a separate slice.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy repository helpers, Elasticsearch script score, pytest.

---

### Task 1: Deal Read Model Interest Signal

**Files:**
- Modify: `apps/api/app/modules/search/indexes.py`
- Modify: `apps/api/app/modules/search/documents.py`
- Modify: `apps/api/app/modules/search/schemas.py`
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/search/use_cases.py`
- Test: `apps/api/tests/test_search_indexes.py`
- Test: `apps/api/tests/test_search_documents.py`
- Test: `apps/api/tests/test_search_rebuild.py`

- [x] Write failing tests that deal mappings and documents include `favoriteCount`.
- [x] Write failing tests that full reindex bulk-loads deal favorite counts and single deal upsert asks the repository for current count.
- [x] Add `ProductRepository.list_deal_favorite_counts()` and `count_deal_favorites()`.
- [x] Pass `favorite_count` into `build_deal_document()`.
- [x] Add `favoriteCount` to the deal index mapping and `DealSearchItem`.
- [x] Run focused tests.

### Task 2: HotDealScore Search Client

**Files:**
- Modify: `apps/api/app/modules/search/client.py`
- Test: `apps/api/tests/test_search_client.py`

- [x] Write a failing test for `ElasticsearchSearchClient.rank_deals()`.
- [x] Add `HOT_DEAL_SCORE_SCRIPT`.
- [x] Implement active-only `script_score` query over `deals_current`.
- [x] Score with capped discount ratio, capped `favoriteCount`, freshness decay, and capped `trustScore`.
- [x] Sort by `_score desc`, `updatedAt desc`, `id desc`.
- [x] Preserve cursor handling with existing `search_after`.

### Task 3: Use Case And Route

**Files:**
- Modify: `apps/api/app/modules/search/use_cases.py`
- Modify: `apps/api/app/modules/search/router.py`
- Test: `apps/api/tests/test_search_api.py`

- [x] Write a failing API test for `GET /api/v1/search/deals/hot?limit=1`.
- [x] Add `SearchUseCases.rank_deals()`.
- [x] Add `/search/deals/hot` before `/search/deals` remains unaffected.
- [x] Return the existing `DealSearchResponse` envelope with cursor.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`

- [x] Document the concrete HotDealScore signal caps and current freshness limitation.
- [x] Add completed hot-deal ranking scope to handoff.
- [x] Run `PYTHONPATH=apps/api uv run pytest apps/api/tests/test_search_client.py apps/api/tests/test_search_api.py apps/api/tests/test_search_documents.py apps/api/tests/test_search_indexes.py apps/api/tests/test_search_rebuild.py -q`.
- [x] Run backend lint/typecheck/tests used by CI.
- [x] Run `git diff --check`.
