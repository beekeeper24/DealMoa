# Search UI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the web shell to the Search Index MVP so users can search products, deals, and auctions from the browser.

**Architecture:** Keep API access in a typed client under `apps/web/src/search`, keep the interactive workspace as a client component, and leave the Next page as a thin server-rendered entry. Tests cover URL construction, UI states, and a browser smoke path with mocked API responses.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, Vitest, Testing Library, Playwright.

---

### Task 1: Search API Client

**Files:**
- Create: `apps/web/src/search/api.ts`
- Create: `apps/web/src/search/types.ts`
- Create: `apps/web/src/search/__tests__/api.test.ts`

- [ ] Write failing tests for product/deal/auction URL construction, cursor handling, and HTTP failure handling.
- [ ] Implement typed `searchProducts`, `searchDeals`, and `searchAuctions`.
- [ ] Run `corepack pnpm --filter @dealmoa/web test`.

### Task 2: Search Workspace UI

**Files:**
- Create: `apps/web/src/search/SearchWorkspace.tsx`
- Create: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/package.json`

- [ ] Write failing tests for initial empty state, successful product search, tab switching, error state, and more-results behavior.
- [ ] Implement the client component using the existing Tailwind tokens.
- [ ] Run `corepack pnpm --filter @dealmoa/web test`.

### Task 3: Browser Smoke

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/search.spec.ts`
- Modify: `apps/web/package.json`

- [ ] Write a Playwright smoke test that mocks `/api/v1/search/products` and verifies browser search results.
- [ ] Add `e2e` script.
- [ ] Run `corepack pnpm --filter @dealmoa/web e2e`.

### Task 4: Verification And Checkpoint

**Files:**
- Modify: `docs/handoff.md`

- [ ] Run API regression checks.
- [ ] Run Web lint, typecheck, test, build, and e2e checks.
- [ ] Start the web dev server and capture a browser screenshot for visual verification.
- [ ] Commit the verified checkpoint on `feature/search-ui-mvp`; do not open a PR until explicitly requested or the slice is ready for integration.
