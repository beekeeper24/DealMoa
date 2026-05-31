# Product Deal Auction Detail MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for behavior changes. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add demoable product, deal, and auction detail pages linked from search results.

**Architecture:** Reuse the existing REST APIs as the source of truth. The web app gets a small typed detail API client, then page components compose product summary, active offers, favorite controls, report submission, and auction bidding without adding new persistence tables in this slice.

**Tech Stack:** Next.js App Router, React, TypeScript, Tailwind CSS, FastAPI REST contracts already implemented.

---

## Scope

- Product detail: show product metadata, specs, current deals, current auctions, and favorite control.
- Deal detail: show deal data, linked product summary, external source link, favorite control, and authenticated report button/form.
- Auction detail: show auction data, linked product summary, external source link, favorite control, authenticated report form, and authenticated bid form using the fixed 1,000 KRW increment.
- Search results link to the corresponding detail pages.

## Non-goals

- No price history, verified reviews, discussions, AI purchase check implementation, or report admin changes in this slice.
- No backend schema changes unless a failing test proves an existing contract is insufficient.
- No realtime auction updates; the page refreshes local state after a successful bid.

## Tasks

### Task 1: Detail API Client

**Files:**
- Create: `apps/web/src/details/types.ts`
- Create: `apps/web/src/details/api.ts`
- Test: `apps/web/src/details/__tests__/api.test.ts`

- [ ] Write failing Vitest coverage for product/deal/auction fetches, bid submission, and report submission.
- [ ] Implement typed fetch helpers using `NEXT_PUBLIC_API_BASE_URL` fallback `/api/v1`.
- [ ] Preserve common API error messages from `{ error: { message } }` responses.

### Task 2: Detail Components

**Files:**
- Create: `apps/web/src/details/ProductDetailPage.tsx`
- Create: `apps/web/src/details/DealDetailPage.tsx`
- Create: `apps/web/src/details/AuctionDetailPage.tsx`
- Test: `apps/web/src/details/__tests__/*.test.tsx`

- [ ] Write failing component tests for loading, success, error, favorite, report, and bid states.
- [ ] Implement product detail with offer lists linking to deal/auction detail pages.
- [ ] Implement deal detail with report submission gated by auth session.
- [ ] Implement auction detail with bid submission gated by auth session and local current-price refresh after success.

### Task 3: Routes And Search Links

**Files:**
- Create: `apps/web/app/products/[productId]/page.tsx`
- Create: `apps/web/app/deals/[dealId]/page.tsx`
- Create: `apps/web/app/auctions/[auctionId]/page.tsx`
- Modify: `apps/web/src/search/SearchWorkspace.tsx`
- Test: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`

- [ ] Add App Router pages that render the corresponding detail component.
- [ ] Link product, deal, and auction search result titles to detail pages.
- [ ] Keep favorite buttons working inside search results.

### Task 4: Browser Smoke

**Files:**
- Create: `apps/web/e2e/detail-pages.spec.ts`
- Modify: `docs/product-api.md`
- Modify: `docs/handoff.md`

- [ ] Add Playwright smoke coverage for product detail navigation from search.
- [ ] Add Playwright smoke coverage for auction bidding from the detail page with mocked APIs.
- [ ] Document the completed detail MVP scope and deferred evidence features.

## Verification

- `corepack pnpm --filter @dealmoa/web test`
- `corepack pnpm --filter @dealmoa/web lint`
- `corepack pnpm --filter @dealmoa/web typecheck`
- `corepack pnpm --filter @dealmoa/web build`
- `corepack pnpm --filter @dealmoa/web e2e`
- `git diff --check`
