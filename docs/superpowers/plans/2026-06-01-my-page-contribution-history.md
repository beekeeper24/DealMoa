# My Page Contribution History Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for authenticated user data exposure and pagination behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal My Page contribution history so authenticated users can see their own submission status without using the admin queue.

**Architecture:** Reuse the existing `GET /api/v1/me/submissions` endpoint and web auth session provider. The web page stays read-only and never calls admin APIs.

**Tech Stack:** FastAPI submissions module, Next.js app route, React client component, Vitest, Playwright.

---

## Scope

- Add `/me` web route for authenticated user contribution history.
- Load `GET /me/submissions` with the in-memory access token from `AuthSessionProvider`.
- Show submission status, offer type, price, source link, AI reason, resolution note, and published offer/product links when available.
- Support cursor pagination with a `더보기` button.
- Link My Page from the search header and from the submission success flow.
- Strengthen backend tests that user submission listing does not expose another user's submissions.

## Non-goals

- No edit/resubmit flow.
- No favorites, notifications, verified reviews, or connected accounts tabs in this slice.
- No new backend endpoint unless the existing one proves insufficient.
- No admin review action from My Page.

## Security Boundaries

- The web page uses only `/me/submissions`.
- It must not call `/admin/submissions`.
- Anonymous users see login guidance only.
- Backend listing remains scoped to `actor.id`.

## Verification

- API tests for own-submission isolation.
- Web unit tests for anonymous, authenticated list, pagination, and admin API non-use.
- Playwright My Page e2e with mocked auth and `/me/submissions`.
- Existing focused submissions tests continue to pass.

## Implementation Checklist

- [x] Add My Page contribution plan.
- [x] Add backend ownership isolation test.
- [x] Add My Page web tests.
- [x] Implement My Page route/component and navigation links.
- [x] Update docs and run focused security review.
