# Notification Web Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing web notification dropdown usable for repeated inbox checks without adding realtime delivery or a dedicated notification page.

**Architecture:** Keep the feature inside `apps/web/src/notifications/NotificationCenter.tsx` and reuse the existing typed API client. The component will manage a compact inbox state machine: recent vs unread filter, cursor-based pagination, read-all refresh, and keyboard/outside-click close behavior.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, Vitest, Testing Library, jsdom.

---

### Task 1: RED Tests For Inbox Polish

**Files:**
- Modify: `apps/web/src/notifications/__tests__/NotificationCenter.test.tsx`

- [ ] **Step 1: Add pagination and unread-filter tests**

Add tests that opening the dropdown can switch to unread-only mode, calls `/api/v1/notifications?limit=20&unreadOnly=true`, renders the unread list, and loads the next page with `cursor=<nextCursor>`.

- [ ] **Step 2: Add close interaction tests**

Add tests that Escape and outside pointer interaction close the open dropdown while preserving the trigger.

- [ ] **Step 3: Run notification component tests and confirm RED**

Run:

```bash
pnpm --dir apps/web vitest run src/notifications/__tests__/NotificationCenter.test.tsx
```

Expected: FAIL because the component does not yet expose unread filtering, pagination, or close interactions.

### Task 2: Implement Notification Dropdown Polish

**Files:**
- Modify: `apps/web/src/notifications/NotificationCenter.tsx`

- [ ] **Step 1: Add local inbox state**

Track `filter`, `nextCursor`, and a root ref for outside-click handling.

- [ ] **Step 2: Add list loading helpers**

Replace the one-shot `refreshNotifications()` with a helper that can load first page or append next page while preserving the current filter.

- [ ] **Step 3: Add interactions**

Add 전체/읽지 않음 filter buttons, a 더보기 button when `nextCursor` exists, Escape close, and outside pointer close.

- [ ] **Step 4: Tighten visual states**

Keep existing palette and compact dropdown shape. Add clearer loading text, disabled states, unread indicators, and `role="dialog"` / `aria-label` on the panel.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
pnpm --dir apps/web vitest run src/notifications/__tests__/NotificationCenter.test.tsx
```

Expected: PASS.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/notifications.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document web polish**

Update docs to mention unread-only filter, cursor-based load more, and keyboard/outside close behavior.

- [ ] **Step 2: Run full web verification**

Run:

```bash
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web build
git diff --check
```

Expected: all pass before commit and PR.
