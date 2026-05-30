# Auction Outbid Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate outbid notifications asynchronously from `auction.bid.placed` events.

**Architecture:** Keep bid placement fast by recording only the previous highest bidder in the outbox payload during the locked API transaction. The notification consumer reads `auction.bid.placed`, validates the previous bidder against persisted auction bids, and creates an idempotent `auction_outbid` notification outside the API request path.

**Tech Stack:** Python 3.12, FastAPI shared domain modules, SQLAlchemy, Kafka consumer boundary, pytest.

---

### Task 1: RED Tests For Payload And Consumer Behavior

**Files:**
- Modify: `apps/api/tests/test_auction_bidding_use_cases.py`
- Modify: `apps/api/tests/test_domain_events_use_cases.py`
- Modify: `apps/consumer/tests/test_domain_event_notifications.py`

- [ ] **Step 1: Add bid payload test**

Add a use-case test where `user-1` already has the highest bid, `user-2` places a higher bid, and the stored `auction.bid.placed` event contains `previousHighestBidderUserId: "user-1"`.

- [ ] **Step 2: Add domain event test**

Extend `DomainEventsUseCases.record_auction_bid_placed()` expectations so callers can pass `previous_highest_bidder_user_id` and the payload stores `previousHighestBidderUserId`.

- [ ] **Step 3: Add consumer notification test**

Add a consumer test where `auction.bid.placed` with `previousHighestBidderUserId` creates exactly one `auction_outbid` notification for the previous bidder, and duplicate delivery remains idempotent.

- [ ] **Step 4: Add no-op cases**

Test that first bids, self-outbids, missing auction, or invalid previous bidder payloads do not create outbid notifications.

- [ ] **Step 5: Run focused tests and confirm RED**

Run: `PYTHONPATH=apps/api:apps/consumer uv run pytest apps/api/tests/test_auction_bidding_use_cases.py apps/api/tests/test_domain_events_use_cases.py apps/consumer/tests/test_domain_event_notifications.py -q`

Expected: FAIL because the payload field, notification type, and consumer handling do not exist yet.

### Task 2: Implement Async Outbid Notification Flow

**Files:**
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/products/use_cases.py`
- Modify: `apps/api/app/modules/events/use_cases.py`
- Modify: `apps/api/app/modules/notifications/models.py`
- Modify: `apps/api/app/modules/notifications/generation.py`
- Modify: `apps/consumer/consumer_app/notification_events.py`

- [ ] **Step 1: Capture previous highest bidder**

Add `ProductRepository.get_highest_auction_bid()` and call it after the auction row is locked but before inserting the new bid.

- [ ] **Step 2: Record previous bidder in outbox**

Pass the previous highest bidder user id to `record_auction_bid_placed()` and include it as `previousHighestBidderUserId`, or `None` for first bids.

- [ ] **Step 3: Add notification type and generator**

Add `NotificationType.AUCTION_OUTBID` and `notify_auction_outbid()` that creates one target notification per `(user, type, auction)`.

- [ ] **Step 4: Handle event in consumer**

For `auction.bid.placed`, load the auction by `aggregateId`, read payload `userId` and `previousHighestBidderUserId`, skip first bids and self-outbids, validate the previous bidder has a bid on the auction, then create the notification.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run the focused pytest command from Task 1 again.

### Task 3: Docs, Verification, And Integration

**Files:**
- Modify: `docs/async-events.md`
- Modify: `docs/product-api.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document async notification behavior**

Update event docs so `auction.bid.placed` is handled by both search indexing and notification generation.

- [ ] **Step 2: Document bid event payload**

Update Product API docs with `previousHighestBidderUserId` semantics.

- [ ] **Step 3: Run full verification**

Run backend/consumer/worker tests, ruff, mypy, compose config, consumer Docker build, `git diff --check`, and focused Kafka notification security grep before commit/PR.
