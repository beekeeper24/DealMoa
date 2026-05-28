# Favorites MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authenticated favorite APIs and a basic web favorite toggle for products, deals, and auctions.

**Architecture:** Keep favorite state in PostgreSQL as user-scoped rows with one unique favorite per target. The API uses the existing auth bearer dependency, thin routers, domain exceptions, repositories, and cursor pagination. The web stores no favorite state outside React component state and calls the API with the current access token.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pytest, Next.js App Router, React, TypeScript, Vitest, Playwright.

---

## Scope

This PR covers favorites only:

- Product, deal, and auction favorite create/delete/list APIs.
- Authenticated current-user enforcement through existing access tokens.
- Web search result favorite buttons with login-required state.
- Docs, handoff, tests, and CI-compatible verification.

Notifications, favorite-driven alerts, my-page aggregation, and ranking signals remain separate PRs.

## File Structure

- Create `apps/api/app/modules/favorites/models.py`: SQLAlchemy models for `product_favorites`, `deal_favorites`, and `auction_favorites`.
- Create `apps/api/app/modules/favorites/repository.py`: user-scoped persistence and cursor list queries.
- Create `apps/api/app/modules/favorites/use_cases.py`: target existence checks, idempotent create/delete behavior, and list orchestration.
- Create `apps/api/app/modules/favorites/schemas.py`: response/list schemas.
- Create `apps/api/app/modules/favorites/router.py`: `/api/v1/me/favorites/...` routes.
- Create `apps/api/alembic/versions/20260528_0003_favorites.py`: favorite tables with unique `(user_id, target_id)` constraints.
- Modify `apps/api/app/api/v1/router.py`: include the favorites router.
- Modify `apps/api/app/core/exceptions.py`: add favorite-specific not-found errors if delete/list cursor input needs stable API codes.
- Create `apps/api/tests/test_favorites_models.py`, `apps/api/tests/test_favorites_use_cases.py`, and `apps/api/tests/test_favorites_api.py`.
- Modify `apps/api/tests/test_alembic_migrations.py`: assert favorite tables exist.
- Modify `apps/web/src/search/types.ts`: add optional favorite fields only if the API response needs them later; for this PR, keep search result contracts unchanged.
- Create `apps/web/src/favorites/api.ts`: typed favorite API client.
- Create `apps/web/src/favorites/FavoriteButton.tsx`: reusable authenticated toggle button.
- Create `apps/web/src/favorites/__tests__/api.test.ts` and `apps/web/src/favorites/__tests__/FavoriteButton.test.tsx`.
- Modify `apps/web/src/search/SearchWorkspace.tsx`: render favorite buttons on product/deal/auction results.
- Modify `apps/web/src/search/__tests__/SearchWorkspace.test.tsx`: assert favorite buttons render and call the API when logged in.
- Modify `apps/web/e2e/search.spec.ts`: include a mocked favorite toggle path.
- Create `docs/favorites.md`: API contract and MVP limitations.
- Modify `docs/handoff.md`: mark Auth MVP completed and make Favorites MVP active.

## API Contract

```http
PUT /api/v1/me/favorites/products/{product_id}
DELETE /api/v1/me/favorites/products/{product_id}
GET /api/v1/me/favorites/products?limit=20&cursor=

PUT /api/v1/me/favorites/deals/{deal_id}
DELETE /api/v1/me/favorites/deals/{deal_id}
GET /api/v1/me/favorites/deals?limit=20&cursor=

PUT /api/v1/me/favorites/auctions/{auction_id}
DELETE /api/v1/me/favorites/auctions/{auction_id}
GET /api/v1/me/favorites/auctions?limit=20&cursor=
```

Create is idempotent and returns the existing favorite if present. Delete is idempotent and returns `204` even when the favorite row is absent, but still returns target not-found when the product/deal/auction does not exist.

## Tasks

### Task 1: Backend Favorite Persistence

- [x] Write model tests for unique user-target favorite constraints and relationships.
- [x] Add favorite SQLAlchemy models and Alembic migration.
- [x] Update migration smoke test to include the three favorite tables.
- [x] Run `uv run pytest apps/api/tests/test_favorites_models.py apps/api/tests/test_alembic_migrations.py -q`.

### Task 2: Backend Favorite Use Cases

- [x] Write use-case tests for create idempotency, delete idempotency, target not-found, per-user isolation, and cursor pagination.
- [x] Implement repository and use-case methods for all three target types.
- [x] Run `uv run pytest apps/api/tests/test_favorites_use_cases.py -q`.

### Task 3: Backend Favorite API

- [x] Write API tests for auth required, create/delete/list success, and target not-found error codes.
- [x] Implement schemas and router under `/api/v1/me/favorites`.
- [x] Include the router from `apps/api/app/api/v1/router.py`.
- [x] Run `uv run pytest apps/api/tests/test_favorites_api.py -q`.

### Task 4: Web Favorite Toggle

- [x] Write Vitest coverage for favorite API requests with bearer token and for logged-in/logged-out button behavior.
- [x] Implement `apps/web/src/favorites/api.ts` and `FavoriteButton.tsx`.
- [x] Wire favorite buttons into product, deal, and auction result rows.
- [x] Run `corepack pnpm --filter @dealmoa/web test`.

### Task 5: Browser Smoke And Docs

- [x] Extend mocked Playwright search smoke with one favorite toggle request.
- [x] Add `docs/favorites.md` and update `docs/handoff.md`.
- [x] Run full validation: API ruff/mypy/pytest, web lint/test/typecheck/build/e2e, compose config, and `git diff --check`.
- [x] Commit as a checkpoint on `feature/favorites-mvp` and push for backup visibility. Do not open a PR until the Favorites MVP slice is verified and coherent.

## Self-Review

- Spec coverage: Milestone 3 favorites are covered; notifications and my-page lists are explicitly deferred.
- Placeholder scan: no `TBD`, `TODO`, or undefined task placeholders are used.
- Type consistency: target names are consistently `product`, `deal`, and `auction`; route paths use plural resource names.
