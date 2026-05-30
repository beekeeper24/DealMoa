# Refresh Session Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop persisting browser access tokens in `sessionStorage` and restore web auth sessions from the API-owned HttpOnly refresh cookie.

**Architecture:** Keep refresh tokens exclusively in the existing API HttpOnly cookie. The web app will hold access tokens only in React memory, call `POST /auth/token/refresh` on mount, and clear any legacy `dealmoa.authSession` value so older local sessions do not keep bearer tokens around.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library, Playwright, FastAPI existing auth API.

---

### Task 1: RED Tests For Non-Persistent Access Tokens

**Files:**
- Modify: `apps/web/src/auth/__tests__/session.test.ts`
- Modify: `apps/web/src/auth/__tests__/AuthCallbackPage.test.tsx`
- Modify: `apps/web/src/auth/__tests__/AuthStatus.test.tsx`
- Modify: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`

- [x] **Step 1: Session storage tests**

Change session tests so storing an auth session is no longer expected. Assert that clearing auth session removes legacy `dealmoa.authSession` values and OAuth state still works.

- [x] **Step 2: Callback tests**

Assert OAuth callback exchanges the code with `credentials: include`, does not write `dealmoa.authSession`, and navigates home after the cookie is set by the API.

- [x] **Step 3: Hook/UI tests**

Assert `AuthStatus` recovers a session by calling `/auth/token/refresh` with `credentials: include`, renders anonymous login buttons when refresh fails, and clears only the legacy client storage on logout.

- [x] **Step 4: Search workspace auth tests**

Update logged-in search tests to mock refresh recovery instead of preloading `sessionStorage`.

- [x] **Step 5: Run focused tests and confirm RED**

Run:

```bash
npm --prefix apps/web test -- src/auth src/search/__tests__/SearchWorkspace.test.tsx
```

Expected: FAIL because the app still reads and writes access-token sessions from `sessionStorage`.

### Task 2: Implement Refresh-Cookie Session Hydration

**Files:**
- Modify: `apps/web/src/auth/session.ts`
- Modify: `apps/web/src/auth/useAuthSession.ts`
- Modify: `apps/web/src/auth/AuthCallbackPage.tsx`
- Modify tests listed in Task 1 as needed

- [x] **Step 1: Restrict session storage**

Keep OAuth state helpers. Remove persistent auth-session reads/writes, and make `clearAuthSession()` remove the legacy `dealmoa.authSession` key.

- [x] **Step 2: Hydrate from refresh cookie**

Update `useAuthSession()` so the first client effect calls `refreshAuthSession()`. On success, store the access token in component state only. On failure, clear legacy storage and set anonymous status.

- [x] **Step 3: Make callback cookie-first**

Update `AuthCallbackPage` so it no longer persists the returned access token. It should rely on the API's Set-Cookie refresh token and navigate home.

- [x] **Step 4: Keep logout behavior**

Keep `logout()` using `credentials: include`, clear legacy storage, and set anonymous state.

- [x] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
npm --prefix apps/web test -- src/auth src/search/__tests__/SearchWorkspace.test.tsx
```

Expected: PASS.

### Task 3: Docs, Security Review, And Integration

**Files:**
- Modify: `docs/auth.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Document token policy**

Update docs to state that web access tokens are memory-only and refreshed from the HttpOnly cookie on mount.

- [x] **Step 2: Run verification**

Run:

```bash
npm --prefix apps/web test
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
npm --prefix apps/web run e2e
git diff --check
```

- [x] **Step 3: Focused security review**

Run a focused grep/review for `sessionStorage`, `localStorage`, `accessToken`, `refreshToken`, `credentials`, `HttpOnly`, and obvious secret leaks in touched auth files and docs.

Result: no high-confidence security finding. Browser-readable storage is limited to OAuth `state` and legacy `dealmoa.authSession` cleanup/tests; callback, refresh, and logout keep `credentials: include`; access tokens are held only in React memory in production code.

Verification evidence:

- `npm --prefix apps/web test`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run typecheck`
- `npm --prefix apps/web run build`
- `npm --prefix apps/web run e2e`
- `git diff --check`
