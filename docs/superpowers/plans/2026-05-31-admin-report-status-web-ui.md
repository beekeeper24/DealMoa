# Admin Report Status Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]` / `- [x]`) syntax for tracking.

**Goal:** Add a web admin report queue that lets admin users review offer reports and optionally change the reported deal or auction status.

**Architecture:** Keep backend contracts unchanged. Add a focused web admin feature under `apps/web/src/admin` with typed API functions, a client component, and tests. Expose the screen through `apps/web/app/admin/page.tsx` and link to it for authenticated admin users from the existing search header.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, Vitest, Testing Library, Playwright.

---

### Task 1: Admin API Client

**Files:**
- Create: `apps/web/src/admin/types.ts`
- Create: `apps/web/src/admin/api.ts`
- Test: `apps/web/src/admin/__tests__/api.test.ts`

- [x] Add report, target summary, list response, review request, and API error types.
- [x] Implement `listAdminReports()` using `GET /api/v1/admin/reports?status=...&limit=20`.
- [x] Implement `reviewAdminReport()` using `PATCH /api/v1/admin/reports/{reportId}`.
- [x] Test auth headers, query params, request body shape, and API error parsing.
- [x] Run `corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts`.

### Task 2: Admin Report Queue Component

**Files:**
- Create: `apps/web/src/admin/AdminReportQueue.tsx`
- Test: `apps/web/src/admin/__tests__/AdminReportQueue.test.tsx`

- [x] Render neutral loading state while auth hydrates.
- [x] Render login-required state for anonymous users.
- [x] Render forbidden state for authenticated non-admin users.
- [x] Render status filters for `open`, `resolved`, and `dismissed`.
- [x] Render report cards with target title, target status, seller, source URL, reason, description, reporter, and created time.
- [x] Add per-card review form with review status, optional target status, and resolution note.
- [x] On successful review, remove the item from the open list when it no longer matches the current filter.
- [x] Test admin load, non-admin guard, resolve with target status, dismiss without target status, error display, and pagination.
- [x] Run `corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/AdminReportQueue.test.tsx`.

### Task 3: Route And Navigation

**Files:**
- Create: `apps/web/app/admin/page.tsx`
- Modify: `apps/web/src/search/SearchWorkspace.tsx`
- Test: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`

- [x] Add `/admin` route rendering `AdminReportQueue`.
- [x] Show an `관리자` link in the existing header only when the hydrated session user role is `ADMIN`.
- [x] Keep search page behavior unchanged for anonymous and regular users.
- [x] Extend the search workspace test to assert the admin link appears only for admin sessions.
- [x] Run `corepack pnpm --filter @dealmoa/web test -- src/search/__tests__/SearchWorkspace.test.tsx`.

### Task 4: Browser Smoke

**Files:**
- Create: `apps/web/e2e/admin-reports.spec.ts`

- [x] Mock admin refresh session, notification count, report list, and report review APIs.
- [x] Visit `/admin`, confirm the report card is visible, resolve it with `targetStatus=rejected`, and confirm the empty state.
- [x] Run `corepack pnpm --filter @dealmoa/web e2e -- admin-reports.spec.ts`.

### Task 5: Verification And Handoff

**Files:**
- Modify: `docs/handoff.md`

- [x] Add completed admin report/status web UI scope.
- [x] Run `corepack pnpm --filter @dealmoa/web test`.
- [x] Run `corepack pnpm --filter @dealmoa/web lint`.
- [x] Run `corepack pnpm --filter @dealmoa/web typecheck`.
- [x] Run focused Playwright smoke for admin reports.
- [x] Run `git diff --check`.
