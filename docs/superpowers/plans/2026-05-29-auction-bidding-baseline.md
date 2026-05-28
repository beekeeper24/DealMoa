# Auction Bidding Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first authenticated auction bid flow that records bids and updates auction activity state.

**Architecture:** Keep the bid baseline inside the existing product/auction module because `Auction` already lives there. A new `auction_bids` table records immutable bid attempts that pass validation, while the existing `auctions.current_price` and `auctions.bid_count` remain the read-optimized auction summary updated in the same transaction. A domain outbox event `auction.bid.placed` is recorded for later Kafka consumers.

**Tech Stack:** FastAPI, SQLAlchemy ORM, Alembic, Pydantic, pytest, existing DealMoa exception handlers.

---

### Task 1: RED Model And Migration Coverage

**Files:**
- Modify: `apps/api/tests/test_product_models.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`

- [x] Add tests that expect an `auction_bids` table with `auction_id`, `user_id`, `amount`, timestamps, indexes for auction/user lookup, and foreign keys to `auctions` and `users`.
- [x] Run the focused tests and confirm they fail because `AuctionBid` and the migration do not exist yet.

### Task 2: RED Use Case And API Coverage

**Files:**
- Create: `apps/api/tests/test_auction_bidding_use_cases.py`
- Create: `apps/api/tests/test_auction_bidding_api.py`
- Modify: `apps/api/tests/test_domain_events_use_cases.py`
- Modify: `apps/api/tests/test_product_domain_events.py`

- [x] Add tests for successful bid placement, bid amount too low, ended auction rejection, missing auction, auth-required API, current-user API wiring, and `auction.bid.placed` outbox payload.
- [x] Run the focused tests and confirm they fail on missing schema/use case/route/event support.

### Task 3: Implement Bid Baseline

**Files:**
- Modify: `apps/api/app/core/exceptions.py`
- Modify: `apps/api/app/modules/products/models.py`
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/products/schemas.py`
- Modify: `apps/api/app/modules/products/use_cases.py`
- Modify: `apps/api/app/modules/products/router.py`
- Modify: `apps/api/app/modules/events/use_cases.py`
- Create: `apps/api/alembic/versions/20260529_0007_auction_bids.py`

- [x] Add `AuctionBid`, exceptions, schemas, repository methods, use case validation, API route, and outbox event support.
- [x] Run the focused tests until they pass.

### Task 4: Documentation And Verification

**Files:**
- Modify: `docs/product-api.md`
- Modify: `docs/api-error-handling.md`
- Modify: `docs/architecture.md`
- Modify: `docs/handoff.md`

- [x] Document `POST /api/v1/auctions/{auction_id}/bids`, response shape, low-bid and ended-auction error codes, and the `auction.bid.placed` event.
- [x] Run API tests, Alembic migration test, focused auth/authorization grep, and diff checks before commit/PR.
