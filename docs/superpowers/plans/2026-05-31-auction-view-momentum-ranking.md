# Auction View Momentum Ranking Implementation Plan

**Goal:** Add the view-momentum signal to auction activity ranking so recently viewed active auctions can gain ranking weight without overriding bid activity.

**Architecture:** Store immutable auction view events in PostgreSQL. The auction detail endpoint records a view and writes `auction.view.recorded` to the transactional outbox. Search documents include `viewMomentum`, computed as the recent view count in a 24-hour window. The Elasticsearch activity script adds a capped 15-point view-momentum contribution.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pytest, Elasticsearch script score, Kafka consumer search refresh boundary.

---

## Task 1: RED Tests

- [x] Add model/migration tests for `auction_views`.
- [x] Add use-case/API tests that auction detail views record one view event and outbox event.
- [x] Add search document/rebuild/indexer tests for `viewMomentum`.
- [x] Add Elasticsearch ranking script tests for `viewMomentum` weight and cap.
- [x] Run focused tests and confirm RED.

## Task 2: Implementation

- [x] Add `AuctionView` model and Alembic migration.
- [x] Add repository methods for recording views and counting recent auction views.
- [x] Add `ProductUseCases.view_auction()` and route auction detail through it.
- [x] Add `record_auction_view_recorded()` domain event and consumer refresh handling.
- [x] Add `viewMomentum` to auction search documents, mappings, rebuilds, and single auction upserts.
- [x] Add `viewMomentum` to the auction activity script with a capped 15-point weight.

## Task 3: Verification And Docs

- [x] Update ranking/handoff/async-event docs.
- [x] Run focused tests.
- [x] Run full API/consumer checks.
- [x] Run focused security/abuse grep for event payloads and unexpected user identifiers.

Verification evidence:

- `uv run pytest tests/test_product_models.py tests/test_product_use_cases.py tests/test_domain_events_use_cases.py tests/test_search_documents.py tests/test_search_indexes.py tests/test_search_client.py tests/test_search_rebuild.py tests/test_search_api.py` from `apps/api`
- `PYTHONPATH=apps/api uv run pytest apps/api/tests/test_alembic_migrations.py`
- `PYTHONPATH=apps/consumer:apps/api uv run --project apps/consumer pytest apps/consumer/tests/test_domain_event_search_indexer.py`
- `uv run ruff check .`
- `uv run mypy apps/api/app apps/api/tests apps/consumer/consumer_app apps/consumer/tests`
- `PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests`
- `npm --prefix apps/web test`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run typecheck`
- `npm --prefix apps/web run build`
- `npm --prefix apps/web run e2e`
- `git diff --check`

Security/abuse review result: no high-confidence finding. `auction.view.recorded` payload contains only `auctionId` and `viewId`; the API does not store user IDs, IP addresses, user-agent strings, or bearer tokens for view momentum.
