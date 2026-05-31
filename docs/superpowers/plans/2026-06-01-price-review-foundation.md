# Price History And Verified Review Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for model, auth, admin approval, state transition, and event behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first price history and verified purchase review foundation so later AI purchase checks can rely on persisted evidence instead of public opinion.

**Architecture:** Keep Product as the aggregate anchor. Store immutable price snapshots for deals and auctions in PostgreSQL, expose product-scoped price history, and add verified review submissions that require AI mock first-pass plus admin approval before they become trusted evidence.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js, React, TypeScript, Tailwind CSS.

---

## Scope

- Store price history snapshots for product, deal/auction source, observed price, currency, and observed time.
- Record price snapshots when deals/auctions are created and when auction bids update current price.
- Expose `GET /api/v1/products/{product_id}/price-history`.
- Authenticated users can submit verified review candidates for a product.
- Mock AI review stores `aiDecision`, `aiReason`, and `aiReviewedAt`.
- Admins can list pending verified reviews.
- Admins can approve or reject verified reviews.
- Product detail can show price history evidence and approved verified reviews.

## Non-goals

- No OCR, receipt image upload, storage, or real purchase provider integration.
- No real AI provider call.
- No score changes from verified reviews yet.
- No dedicated My Page review history.
- No discussion/community thread implementation.

## API Contract

```http
GET /api/v1/products/{product_id}/price-history
POST /api/v1/products/{product_id}/verified-reviews
GET /api/v1/products/{product_id}/verified-reviews
GET /api/v1/admin/verified-reviews?status=pending_review
PATCH /api/v1/admin/verified-reviews/{review_id}
```

Verified review statuses:

- `pending_review`: created and AI mock reviewed, awaiting admin.
- `approved`: admin approved and safe for purchase-check evidence.
- `rejected`: admin rejected.

Admin actions:

- `approve`
- `reject`

## Verification

- API focused tests for model, migration, use case, router, and price snapshot side effects.
- Web API/component tests for product detail evidence rendering and review submission.
- Playwright smoke for product detail price/review evidence with mocked APIs.
- Full local API/Web lint, typecheck, tests, build, and e2e before PR.

## Implementation Checklist

- [x] Add price-history and verified-review tables plus migration coverage.
- [x] Record price snapshots on deal creation, auction creation, and accepted auction bids.
- [x] Add authenticated verified-review submission and admin approval/rejection APIs.
- [x] Emit `review.verified` only after admin approval.
- [x] Separate public approved-review response from admin/creator metadata response.
- [x] Render price history and approved verified reviews on product detail.
- [x] Document evidence boundaries and security/privacy decisions.
