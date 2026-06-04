# Admin Discussion Moderation UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #55 so admins can review visible/hidden product discussion comments and hide or restore them from the web admin console.

**Architecture:** Reuse the existing admin discussion API: `GET /api/v1/admin/discussions?status=...` and `PATCH /api/v1/admin/discussions/{commentId}`. Add typed admin web client functions and a dedicated client component under `apps/web/src/admin`. Do not add new moderation states, spam scoring, or backend domain behavior.

**Tech Stack:** Next.js, React, TypeScript, Tailwind CSS, Vitest, Testing Library, existing FastAPI discussion API.

---

## File Structure

- Modify `apps/web/src/admin/types.ts`
  - Add discussion status, comment, list response, and moderation request types.
- Modify `apps/web/src/admin/api.ts`
  - Add `listAdminDiscussions` and `moderateAdminDiscussion`.
- Create `apps/web/src/admin/AdminDiscussionModerationPage.tsx`
  - Admin-only queue UI with visible/hidden tabs, cards, moderation note, hide/restore action, pagination, and links to other admin pages.
- Create `apps/web/app/admin/discussions/page.tsx`
  - Next.js route that renders `AdminDiscussionModerationPage`.
- Modify existing admin navigation components
  - Add links to `/admin/discussions` from report, crawler, and submission admin pages where those pages already show admin cross-links.
- Modify `apps/web/src/admin/__tests__/api.test.ts`
  - Add client tests for listing and hide/restore PATCH requests.
- Create `apps/web/src/admin/__tests__/AdminDiscussionModerationPage.test.tsx`
  - Add admin UI tests for anonymous, non-admin, list/filter, hide, restore, and API error behavior.
- Modify `docs/discussions.md` and `docs/handoff.md`
  - Mark dedicated admin discussion web queue as completed and record remaining non-goals.

## Task 1: Web API Client Red Tests

**Files:**
- Modify: `apps/web/src/admin/__tests__/api.test.ts`

- [x] **Step 1: Add failing API client tests**

Add imports for `listAdminDiscussions` and `moderateAdminDiscussion`.

Add tests that expect:

```typescript
await listAdminDiscussions({
  accessToken: "access-1",
  cursor: "cursor-1",
  status: "visible"
});
```

to call:

```typescript
"/api/v1/admin/discussions?status=visible&limit=20&cursor=cursor-1"
```

Add a moderation test that expects:

```typescript
await moderateAdminDiscussion({
  accessToken: "access-1",
  action: "hide",
  commentId: "discussion-1",
  moderationNote: "욕설 포함"
});
```

to call:

```typescript
"/api/v1/admin/discussions/discussion-1"
```

with body:

```json
{"action":"hide","moderationNote":"욕설 포함"}
```

- [x] **Step 2: Run API client red tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts
```

Expected: fail because the two functions do not exist.

## Task 2: Web Page Red Tests

**Files:**
- Create: `apps/web/src/admin/__tests__/AdminDiscussionModerationPage.test.tsx`

- [x] **Step 1: Add failing page tests**

Cover:

- anonymous users see `관리자 로그인이 필요합니다.`;
- non-admin users see `관리자 권한이 필요합니다.`;
- admins load visible comments and can hide one;
- admins switch to hidden comments and can restore one;
- admin API errors show the server message.

Use the existing `AuthSessionProvider` test pattern from `AdminReportQueue.test.tsx`.

- [x] **Step 2: Run page red tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/AdminDiscussionModerationPage.test.tsx
```

Expected: fail because `AdminDiscussionModerationPage` does not exist.

## Task 3: Web Implementation

**Files:**
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/api.ts`
- Create: `apps/web/src/admin/AdminDiscussionModerationPage.tsx`
- Create: `apps/web/app/admin/discussions/page.tsx`
- Modify: `apps/web/src/admin/AdminReportQueue.tsx`
- Modify: `apps/web/src/admin/AdminCrawlerRunLogPage.tsx`
- Modify: `apps/web/src/submissions/AdminSubmissionQueue.tsx`

- [x] **Step 1: Add admin discussion types**

Add:

```typescript
export type AdminDiscussionStatus = "visible" | "hidden";
export type AdminDiscussionModerationAction = "hide" | "restore";
```

Add `AdminDiscussionComment`, `AdminDiscussionListResponse`, and `AdminDiscussionModerationRequest`.

- [x] **Step 2: Add API client functions**

Implement:

```typescript
export async function listAdminDiscussions(...)
export async function moderateAdminDiscussion(...)
```

Reuse `authHeaders`, `parseJson`, and `throwAdminReportError`.

- [x] **Step 3: Add page component and route**

Build a simple admin queue:

- tabs: `공개 댓글`, `숨김 댓글`;
- cards show nickname, product id, body, status, created time, moderation note when present;
- visible cards use action `hide`;
- hidden cards use action `restore`;
- optional moderation note textarea;
- action success removes the item from the current filtered list;
- `더보기` uses `nextCursor`.

- [x] **Step 4: Add admin navigation links**

Add `토론 검토` links to existing admin pages so the queue is reachable.

- [x] **Step 5: Run green tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/api.test.ts src/admin/__tests__/AdminDiscussionModerationPage.test.tsx
```

Expected: tests pass.

## Task 4: Docs, Verification, and Security Review

**Files:**
- Modify: `docs/discussions.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Update docs**

Document:

- `/admin/discussions` is now available;
- public responses still exclude admin/internal fields;
- admin queue can only hide/restore, not edit comment bodies;
- spam scoring, rate limits, author edit/delete, and nested replies remain deferred.

- [x] **Step 2: Run verification**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests/test_discussions_api.py -q
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
git diff --check
```

- [x] **Step 3: Focused security review**

Review the diff for:

- admin-only UI access;
- bearer token sent on admin endpoints;
- public/internal field separation;
- no raw HTML rendering of comment bodies;
- no comment body edit/delete path added.
