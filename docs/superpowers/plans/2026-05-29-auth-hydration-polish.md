# Auth Hydration Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep auth-dependent web UI stable between server render and browser hydration.

**Architecture:** Add a small client-side auth session hook that starts in a neutral loading state and reads `sessionStorage` only after mount. Reuse that state in the search workspace header so auth status, notifications, and favorite controls are derived from one browser-only session snapshot.

**Tech Stack:** Next.js client components, React hooks, TypeScript, Vitest, Testing Library.

---

### Task 1: Lock The Hydration Contract With Tests

**Files:**
- Modify: `apps/web/src/auth/__tests__/AuthStatus.test.tsx`
- Modify: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`

- [ ] Add server-render tests proving auth UI does not commit login/authenticated controls before the browser session check.
- [ ] Run the focused tests and confirm they fail against the current `sessionStorage` render-time reads.

### Task 2: Add Browser-Only Auth Session State

**Files:**
- Create: `apps/web/src/auth/useAuthSession.ts`
- Modify: `apps/web/src/auth/AuthStatus.tsx`
- Modify: `apps/web/src/search/SearchWorkspace.tsx`

- [ ] Implement `useAuthSession()` with `loading`, `authenticated`, and `anonymous` states.
- [ ] Render a stable auth placeholder while the session is loading.
- [ ] Pass the shared auth state from `SearchWorkspace` to `AuthStatus`, `NotificationCenter`, and search result favorite buttons.

### Task 3: Document And Verify

**Files:**
- Modify: `docs/auth.md`
- Modify: `docs/handoff.md`

- [ ] Document that the MVP web access token remains in `sessionStorage`, but auth-dependent UI only reads it after mount.
- [ ] Run web lint, typecheck, focused tests, full web tests, build, and focused security grep.
- [ ] Commit the verified slice in Korean, push the branch, open/merge PR only after the slice is coherent and checks pass.
