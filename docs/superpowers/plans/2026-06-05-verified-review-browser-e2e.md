# Verified Review Browser E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cover verified-review auto-publish and duplicate-submit behavior in Playwright browser smoke tests.

**Architecture:** Keep Playwright tests fully mocked at the HTTP boundary, matching current e2e style. Extend product detail e2e only, because the browser behavior under test lives on the product detail page. Do not change production UI unless the test exposes a real bug.

**Tech Stack:** Next.js, Playwright, mocked API routes, existing pnpm scripts.

---

### Task 1: Product Detail Verified Review E2E

**Files:**
- Modify: `apps/web/e2e/detail-pages.spec.ts`

- [x] Update the existing product detail public verified-review mock to match `PublicVerifiedReviewResponse`.
- [x] Assert public detail does not render proof references, AI review reason, reviewer id, or resolution note.
- [x] Add a logged-in product detail e2e path that submits a verified review successfully.
- [x] Assert the POST request includes bearer auth and the trimmed review payload.
- [x] Assert the page shows `인증 후기가 공개되었습니다.` and renders the newly created review.
- [x] Add a duplicate submission path that returns `VERIFIED_REVIEW_ALREADY_EXISTS`.
- [x] Assert the duplicate error message is displayed to the user.

### Task 2: Docs And Verification

**Files:**
- Modify: `docs/handoff.md`
- Modify: `docs/performance.md`

- [x] Document that browser smoke e2e now covers verified-review submit success and duplicate error handling.
- [x] Run `corepack pnpm --filter @dealmoa/web e2e`.
- [x] Run web lint/test/typecheck/build.
- [x] Run backend checks only if API or backend docs are changed.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync `develop`, and create Notion work log.
