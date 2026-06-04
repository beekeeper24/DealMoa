# Admin Verified Review Moderation UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin web UI for post-publication moderation of auto-published verified purchase reviews.

**Architecture:** Keep the backend contract unchanged: admins list verified reviews by status and PATCH a moderation action. The web app adds typed API helpers and one focused admin page that follows the existing discussion moderation UI pattern.

**Tech Stack:** Next.js, React, TypeScript, Vitest, Testing Library, existing FastAPI admin verified-review API.

---

### Task 1: Policy Documentation

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/planning.md`
- Modify: `docs/price-reviews.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`

- [x] Replace consumer-report-centered wording such as `reported`, `신고 누적`, and `신고된 인증 후기` with platform-risk/admin-review wording.
- [x] State that the MVP does not prioritize a consumer report button for verified reviews.
- [x] Keep the existing rule that public product detail returns only `approved` reviews and hides proof/moderation metadata.

### Task 2: Web API TDD

**Files:**
- Modify: `apps/web/src/admin/__tests__/api.test.ts`
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/api.ts`

- [x] Add a failing test for `listAdminVerifiedReviews()`:

```ts
const page = await listAdminVerifiedReviews({
  accessToken: "access-1",
  cursor: "cursor-1",
  status: "approved"
});

expect(fetchMock).toHaveBeenCalledWith(
  "/api/v1/admin/verified-reviews?status=approved&limit=20&cursor=cursor-1",
  { headers: { Accept: "application/json", Authorization: "Bearer access-1" } }
);
expect(page.items[0].proofReference).toBe("order-123");
```

- [x] Add a failing test for `moderateAdminVerifiedReview()`:

```ts
const result = await moderateAdminVerifiedReview({
  accessToken: "access-1",
  action: "hide",
  reviewId: "review-1",
  resolutionNote: "허위 증빙"
});

expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/verified-reviews/review-1", {
  body: JSON.stringify({ action: "hide", resolutionNote: "허위 증빙" }),
  headers: {
    Accept: "application/json",
    Authorization: "Bearer access-1",
    "Content-Type": "application/json"
  },
  method: "PATCH"
});
expect(result.status).toBe("hidden");
```

- [x] Run `corepack pnpm --filter @dealmoa/web test src/admin/__tests__/api.test.ts` and confirm the new tests fail because the helpers do not exist.
- [x] Add verified-review admin types and API helpers.
- [x] Re-run the focused API test and confirm it passes.

### Task 3: Admin Page TDD

**Files:**
- Create: `apps/web/src/admin/AdminVerifiedReviewModerationPage.tsx`
- Create: `apps/web/src/admin/__tests__/AdminVerifiedReviewModerationPage.test.tsx`
- Create: `apps/web/app/admin/verified-reviews/page.tsx`
- Modify: existing admin page links as needed

- [x] Add failing UI tests for:
  - anonymous users seeing `관리자 로그인이 필요합니다.`;
  - non-admin users seeing `관리자 권한이 필요합니다.`;
  - admins loading `approved` reviews and hiding one with `resolutionNote`;
  - admins switching to `hidden`, restoring one, and using cursor pagination;
  - no consumer report button/text being rendered.
- [x] Run `corepack pnpm --filter @dealmoa/web test src/admin/__tests__/AdminVerifiedReviewModerationPage.test.tsx` and confirm failures are from the missing page.
- [x] Implement the page using existing admin auth/session and moderation-card patterns.
- [x] Add route `app/admin/verified-reviews/page.tsx`.
- [x] Re-run the focused UI test and confirm it passes.

### Task 4: Verification And Integration

**Files:**
- Update touched docs and web files only.

- [x] Run frontend checks:

```bash
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
```

- [x] Run backend regression checks:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
git diff --check
```

- [x] Run a focused security review for admin authorization and proof-reference exposure.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync local `develop`, and update the Notion work log.
