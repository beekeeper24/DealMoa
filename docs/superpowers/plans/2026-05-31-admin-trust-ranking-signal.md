# Admin Trust Ranking Signal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect existing offer `status` values to search visibility gates and auction trust ranking.

**Architecture:** PostgreSQL remains the source of truth for Deal/Auction status. Elasticsearch documents gain an explicit `trustScore` read-model field derived from status, general offer search filters to active documents, and auction activity ranking adds the documented 5-point Trust contribution.

**Tech Stack:** FastAPI, SQLAlchemy models, Elasticsearch mappings/script score, Pydantic response schemas, Next.js TypeScript types, pytest.

---

### Task 1: Search Document And Mapping

**Files:**
- Modify: `apps/api/app/modules/search/documents.py`
- Modify: `apps/api/app/modules/search/indexes.py`
- Test: `apps/api/tests/test_search_documents.py`
- Test: `apps/api/tests/test_search_indexes.py`

- [x] Add failing document tests that assert active deals get `trustScore == 10`, active auctions get `trustScore == 5`, and non-active offers get `trustScore == 0`.
- [x] Add failing mapping tests that assert deal and auction mappings expose `trustScore` as an integer.
- [x] Implement a small status-to-trust helper in `documents.py`.
- [x] Add `trustScore` to deal and auction document builders and mappings.
- [x] Run `uv run pytest apps/api/tests/test_search_documents.py apps/api/tests/test_search_indexes.py`.

### Task 2: Search Visibility Gate And Auction Trust Ranking

**Files:**
- Modify: `apps/api/app/modules/search/client.py`
- Test: `apps/api/tests/test_search_client.py`

- [x] Add a failing client test that deal and auction general search wrap text search in a bool query with `status = active`.
- [x] Extend the auction activity test to assert the script references `trustScore` and uses `trustScoreWeight == 5.0`.
- [x] Implement the active offer filter for deal/auction search while leaving product search unchanged.
- [x] Add capped trust contribution to `AUCTION_ACTIVITY_SCRIPT`.
- [x] Run `uv run pytest apps/api/tests/test_search_client.py`.

### Task 3: API/Web Types And Docs

**Files:**
- Modify: `apps/api/app/modules/search/schemas.py`
- Modify: `apps/api/tests/test_search_api.py`
- Modify: `apps/web/src/search/types.ts`
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`

- [x] Add `trustScore` to Deal/Auction search response schemas and fake API test payloads.
- [x] Add optional `trustScore` to web search result types.
- [x] Update ranking docs to mark Trust as implemented from status-derived read-model score.
- [x] Update handoff completed scope and next activation steps.

### Task 4: Verification And Integration

**Files:**
- All changed files

- [ ] Run focused API tests for search document, index, client, rebuild, API, and consumer indexing.
- [ ] Run backend lint/type/test verification: `uv run ruff check .`, `uv run mypy ...`, full pytest.
- [ ] Run web test/lint/typecheck/build/e2e if TypeScript changed.
- [ ] Commit with a Korean message, push the feature branch, open PR to `develop`, wait for CI, squash merge, and sync local `develop`.
- [ ] Create a Notion work log under `작업일지 > DealMoa`.
