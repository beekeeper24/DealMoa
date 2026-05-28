# Auth HttpOnly Cookie Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move refresh-token transport from browser-readable JSON/sessionStorage into an HttpOnly cookie before Auth MVP integration.

**Architecture:** The API still stores hashed refresh tokens and rotates them server-side, but sends the raw refresh token only as `dm_refresh_token` HttpOnly cookie. Web code stores only the access token and user in `sessionStorage`, and uses `credentials: "include"` for callback, refresh, and logout.

**Tech Stack:** FastAPI cookies, Pydantic schemas, React/Next.js client components, Vitest, Pytest, Playwright.

---

### Task 1: API Cookie Contract

**Files:**
- Modify: `apps/api/app/modules/auth/router.py`
- Modify: `apps/api/app/modules/auth/schemas.py`
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/tests/test_auth_api.py`

- [x] **Step 1: Write failing API tests**

Assert callback and refresh responses omit `refreshToken`, set `dm_refresh_token` HttpOnly cookie, refresh/logout read cookie, and missing cookie returns `INVALID_REFRESH_TOKEN`.

- [x] **Step 2: Implement API cookie helpers**

Set cookie on callback/refresh and delete cookie on logout. Use `HttpOnly`, `SameSite=lax`, configurable `Secure`, path `/api/v1/auth`, and max age matching refresh expiry days.

### Task 2: Web Token Storage Contract

**Files:**
- Modify: `apps/web/src/auth/types.ts`
- Modify: `apps/web/src/auth/session.ts`
- Modify: `apps/web/src/auth/api.ts`
- Modify: `apps/web/src/auth/AuthStatus.tsx`
- Modify: `apps/web/src/auth/__tests__/*.ts*`
- Modify: `apps/web/e2e/auth.spec.ts`

- [x] **Step 1: Write failing web tests**

Assert session storage no longer contains refresh tokens and auth fetch calls use `credentials: "include"`.

- [x] **Step 2: Implement web changes**

Remove `refreshToken` from `AuthSession`; update logout/refresh to require no token argument; include credentials on cookie-writing/reading requests.

### Task 3: CORS, Docs, Verification

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `docs/auth.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Add credentialed CORS settings**

Expose `API_CORS_ORIGINS`, `AUTH_REFRESH_COOKIE_SECURE`, and cookie settings through config/compose.

- [x] **Step 2: Document the final MVP auth transport**

Record that refresh tokens are HttpOnly cookie-only and access tokens remain short-lived browser state.

- [x] **Step 3: Verify and commit**

Run API/web lint, typecheck, tests, build, e2e, compose config, focused auth security grep, and push the feature branch without opening a PR.
