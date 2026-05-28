# Notification Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a usable authenticated notification dropdown to the web search workspace.

**Architecture:** Keep notification API access in a small `src/notifications/api.ts` client and render a `NotificationCenter` client component in the existing search header. The component uses the stored access token from the current MVP session, fetches unread count on mount, fetches recent notifications when opened, and supports mark-read and read-all actions.

**Tech Stack:** Next.js, React, TypeScript, Tailwind CSS, Vitest, Testing Library, Playwright.

---

## Scope

- Typed web client for notification list, unread count, mark read, and read all.
- Header notification dropdown for logged-in users.
- Loading, empty, unread, read, error, and action states.
- Documentation/handoff update.

Out of scope:

- Push/email delivery.
- Realtime websocket/SSE updates.
- Dedicated full notification page.

## Design

- Visual thesis: extend the existing calm paper/ink/signal UI with a compact operational dropdown, not a marketing panel.
- Content plan: notification trigger in header, recent notification list, per-item read action, read-all action.
- Interaction plan: dropdown open/close, hover/focus affordances, optimistic refresh after read actions.

## Tasks

### Task 1: Notification API Client

**Files:**
- Create: `apps/web/src/notifications/types.ts`
- Create: `apps/web/src/notifications/api.ts`
- Test: `apps/web/src/notifications/__tests__/api.test.ts`

- [x] Write failing tests for unread count, list, mark read, read all, and API error handling.
- [x] Implement typed notification client functions.
- [x] Verify focused API tests pass.

### Task 2: Notification Center Component

**Files:**
- Create: `apps/web/src/notifications/NotificationCenter.tsx`
- Test: `apps/web/src/notifications/__tests__/NotificationCenter.test.tsx`
- Modify: `apps/web/src/search/SearchWorkspace.tsx`

- [x] Write failing tests for hidden logged-out state, unread count fetch, dropdown list, mark read, and read all.
- [x] Implement `NotificationCenter` with existing Tailwind patterns.
- [x] Mount it in the search header when an access token exists.
- [x] Verify focused component/search tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/notifications.md`
- Modify: `docs/handoff.md`

- [x] Document the web dropdown scope.
- [x] Update handoff active/completed sections.
- [x] Run web lint/typecheck/test/build, Playwright/screenshot verification, backend smoke checks, Docker Compose config, and `git diff --check`.
