# Auth Web MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first usable web login flow for Google, Kakao, and Naver OAuth on top of the existing Auth API.

**Architecture:** Keep auth UI and auth API client code inside `apps/web/src/auth`. The browser starts login by requesting an authorization URL from the API, stores a short-lived OAuth state in `sessionStorage`, redirects to the provider, verifies state on callback, exchanges the code through the API, then stores the returned session in `sessionStorage` for the MVP.

**Tech Stack:** Next.js App Router, React client components, TypeScript, Tailwind CSS, Vitest, Testing Library, Playwright.

---

### Task 1: Auth Client And Session Store

**Files:**
- Create: `apps/web/src/auth/types.ts`
- Create: `apps/web/src/auth/session.ts`
- Create: `apps/web/src/auth/api.ts`
- Test: `apps/web/src/auth/__tests__/session.test.ts`
- Test: `apps/web/src/auth/__tests__/api.test.ts`

- [x] **Step 1: Write failing tests for session storage**

Cover state generation, state validation, session persistence, and malformed stored session fallback.

- [x] **Step 2: Implement minimal session storage**

Use `sessionStorage`, not `localStorage`. Store only the returned MVP session and a provider-scoped OAuth state.

- [x] **Step 3: Write failing tests for Auth API client**

Cover authorize-url request, callback exchange, `/me` with bearer token, common error response handling, and logout/refresh payloads.

- [x] **Step 4: Implement Auth API client**

Follow the existing search client pattern and common API error shape.

### Task 2: Login Surface In Search Workspace

**Files:**
- Create: `apps/web/src/auth/AuthStatus.tsx`
- Modify: `apps/web/src/search/SearchWorkspace.tsx`
- Test: `apps/web/src/auth/__tests__/AuthStatus.test.tsx`
- Test: `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`

- [x] **Step 1: Write failing UI tests**

Verify provider buttons render, clicking Google requests an authorize URL and redirects, current session shows the user's email, and logout clears session.

- [x] **Step 2: Implement AuthStatus**

Use the existing restrained header style. Keep provider buttons compact and operational, with loading/error states.

- [x] **Step 3: Mount AuthStatus in the header**

Add it to the existing header row without changing search behavior.

### Task 3: OAuth Callback Page

**Files:**
- Create: `apps/web/app/auth/callback/[provider]/page.tsx`
- Create: `apps/web/src/auth/AuthCallbackPage.tsx`
- Test: `apps/web/src/auth/__tests__/AuthCallbackPage.test.tsx`
- Test: `apps/web/e2e/auth.spec.ts`

- [x] **Step 1: Write failing callback tests**

Cover missing code/state, state mismatch, successful callback exchange, session storage, and redirect back to `/`.

- [x] **Step 2: Implement callback page**

Use `useSearchParams`, verify `state`, exchange `code`, persist session, then replace navigation to `/`.

- [x] **Step 3: Add Playwright smoke**

Mock API responses and verify login redirect plus callback storage behavior in Chromium.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/auth.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Document frontend auth behavior**

Record callback routes, sessionStorage MVP decision, and later migration target to server-managed HttpOnly cookies.

- [ ] **Step 2: Run verification**

Run API/web lint, typecheck, tests, build, e2e, Docker Compose config, focused auth security grep, and browser screenshot/smoke.

- [ ] **Step 3: Commit and push**

Commit in Korean on `feature/auth-mvp` and push the branch. Do not open a PR unless explicitly requested.
