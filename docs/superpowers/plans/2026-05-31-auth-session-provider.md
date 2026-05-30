# Auth Session Provider Implementation Plan

**Goal:** Make web auth session state a single source of truth so page-level UI, auth controls, notifications, and favorite buttons share one refresh-cookie hydration result.

**Architecture:** Add an `AuthSessionProvider` client component at the app root. The provider owns the in-memory access token and calls `POST /auth/token/refresh` once on mount. `useAuthSession()` becomes a context consumer, so multiple components can read the same session snapshot without triggering duplicate refresh token rotation.

**Tech Stack:** Next.js 15, React 19, TypeScript, Vitest, Testing Library, Playwright.

---

## Task 1: RED Tests

- [x] Add tests showing two auth consumers under one provider trigger only one refresh request.
- [x] Update search workspace tests so the workspace is rendered under the provider and still gets one shared session.
- [x] Update auth status tests to wrap hook consumers in the provider.
- [x] Run focused tests and confirm failure before implementation.

## Task 2: Provider Implementation

- [x] Add `AuthSessionProvider` and `AuthSessionContext`.
- [x] Move refresh-cookie hydration state from `useAuthSession()` into the provider.
- [x] Make `useAuthSession()` read the context and throw a clear error outside the provider.
- [x] Wrap the Next root layout body with the provider.
- [x] Keep OAuth callback, logout, and legacy storage cleanup behavior unchanged.

## Task 3: Verification And Documentation

- [x] Update docs to record that auth session state is app-root scoped.
- [x] Run focused auth/search tests.
- [x] Run full web test, lint, typecheck, build, e2e, and `git diff --check`.
- [x] Run focused security grep for auth/session/token/cookie storage patterns.

Verification evidence:

- `npm --prefix apps/web test -- src/auth src/search/__tests__/SearchWorkspace.test.tsx`
- `npm --prefix apps/web test`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run typecheck`
- `npm --prefix apps/web run build`
- `npm --prefix apps/web run e2e`
- `git diff --check`

Security review result: no high-confidence finding. Access tokens remain React memory-only, refresh/callback/logout still use cookie credentials, and browser-readable storage remains limited to OAuth `state` plus legacy `dealmoa.authSession` cleanup/tests.
