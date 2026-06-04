# My Verified Review History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #62 so authenticated users can see their own verified-review history from My Page.

**Architecture:** Reuse the existing evidence module and `VerifiedReviewResponse` for authenticated self-history because the user is allowed to see their own proof metadata and AI/admin review state. Add a dedicated `/api/v1/me/verified-reviews` route that filters by current user and uses the same cursor pagination shape as `/api/v1/me/submissions`. Extend the existing `/me` web page with a second history section instead of creating a separate page.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Next.js, React, TypeScript, Vitest, pytest.

---

## File Structure

- Modify `apps/api/app/modules/evidence/repository.py`
  - Add `list_user_verified_reviews(user_id, limit, cursor)`.
- Modify `apps/api/app/modules/evidence/use_cases.py`
  - Add `list_my_verified_reviews(actor, limit, cursor)`.
- Modify `apps/api/app/modules/evidence/router.py`
  - Add `me_router = APIRouter(prefix="/me/verified-reviews")` and route.
- Modify `apps/api/app/api/v1/router.py`
  - Include the new evidence `me_router`.
- Modify `apps/api/tests/test_evidence_api.py`
  - Add authenticated self-history test and non-admin/no-cross-user assertion.
- Create `apps/web/src/me/api.ts`
  - My Page specific API client for submissions and verified-review history.
- Create `apps/web/src/me/types.ts`
  - Shared My Page history types.
- Modify `apps/web/src/me/MyPage.tsx`
  - Fetch submissions and verified reviews after auth hydration.
  - Render two sections with independent errors and pagination.
- Modify `apps/web/src/me/__tests__/MyPage.test.tsx`
  - Assert both histories load and no admin APIs are called.
- Create or modify `apps/web/src/me/__tests__/api.test.ts`
  - Assert `/me/submissions` and `/me/verified-reviews` request paths/headers.
- Modify `docs/price-reviews.md`, `docs/handoff.md`
  - Document the self-history API and My Page behavior.

## Task 1: API RED Tests

- [x] **Step 1: Add failing API test**

Add a test in `apps/api/tests/test_evidence_api.py` that:

- creates two users;
- creates verified reviews for both users;
- calls `GET /api/v1/me/verified-reviews?limit=1` as `user-1`;
- asserts only `user-1` reviews appear;
- follows `nextCursor`;
- asserts `proofReference`, `aiReason`, `resolutionNote`, and status are present for the owner.

- [x] **Step 2: Run API RED command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_evidence_api.py -q
```

Expected: fail because `/api/v1/me/verified-reviews` does not exist.

## Task 2: API Implementation

- [x] **Step 1: Add repository/use-case method**

Add self-history query ordered by:

```text
created_at DESC, id DESC
```

Cursor validation must require the cursor row to belong to the same user.

- [x] **Step 2: Add router and include it**

Return `VerifiedReviewListResponse` from `GET /api/v1/me/verified-reviews`.

- [x] **Step 3: Run API GREEN command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_evidence_api.py -q
```

Expected: pass.

## Task 3: Web RED Tests

- [x] **Step 1: Add My Page API client tests**

Assert:

- `listMySubmissions` calls `/me/submissions?limit=20`;
- `listMyVerifiedReviews` calls `/me/verified-reviews?limit=20`;
- both attach the bearer token.

- [x] **Step 2: Add My Page UI test expectations**

Update `MyPage.test.tsx` so the authenticated flow expects both:

- submission history card;
- verified-review history card with status, rating, AI reason, and resolution note.

- [x] **Step 3: Run Web RED command**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/me/__tests__/MyPage.test.tsx src/me/__tests__/api.test.ts
```

Expected: fail because the My Page API module and review section do not exist.

## Task 4: Web Implementation

- [x] **Step 1: Add `src/me/api.ts` and `src/me/types.ts`**

Move My Page read APIs into a me-specific module and include both list methods.

- [x] **Step 2: Render verified-review history**

Keep the UI compact and utilitarian:

- submissions section;
- verified reviews section;
- independent pagination buttons;
- authenticated-only fetches;
- no admin API calls.

- [x] **Step 3: Run Web GREEN command**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/me/__tests__/MyPage.test.tsx src/me/__tests__/api.test.ts
```

Expected: pass.

## Task 5: Docs, Verification, and Integration

- [x] **Step 1: Update docs**

Document:

- `GET /api/v1/me/verified-reviews`;
- owner-only response boundary;
- My Page now includes submissions and verified reviews;
- favorites/notifications/connected accounts remain deferred.

- [x] **Step 2: Security review**

Check:

- self-history filters by current user;
- no admin verified-review API is called from My Page;
- public verified-review response remains proof/AI/admin safe;
- no raw HTML rendering.

- [x] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
git diff --check
```

- [ ] **Step 4: Commit and integrate**

Commit, push `feature/my-verified-review-history`, open PR to `develop`, wait for CI, merge if green, sync local `develop`, and write a Notion work log.

## Self-Review

- Spec coverage: issue #62 criteria map to API tests, Web tests, docs, and security review.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: API returns existing `VerifiedReviewResponse`; Web reuses the same shape in a My Page type module.
