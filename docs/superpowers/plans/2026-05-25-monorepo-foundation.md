# Monorepo Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first PR-sized DealMoa monorepo foundation: API, Web, Docker Compose core profile, environment example, and CI.

**Architecture:** Keep the scaffold conventional and thin. FastAPI owns `/health` and `/api/v1/health`; Next.js owns the initial product-centered search shell; Docker Compose wires the core local runtime.

**Tech Stack:** FastAPI, uv, pytest, ruff, mypy, Next.js, React, TypeScript, Tailwind CSS, pnpm, Vitest, PostgreSQL, Redis, Elasticsearch with Nori, GitHub Actions.

---

### Task 1: Backend Workspace And Health API

**Files:**
- Create: `pyproject.toml`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/main.py`
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/app/api/v1/router.py`
- Create: `apps/api/app/api/v1/routes/health.py`
- Create: `apps/api/tests/test_health.py`

- [x] Add the uv workspace and API package.
- [x] Add a FastAPI app factory with `/health` and `/api/v1/health`.
- [x] Add pytest coverage for both health endpoints.
- [x] Verify with `uv run ruff check apps/api`, `uv run mypy apps/api/app apps/api/tests`, and `uv run pytest apps/api/tests`.

### Task 2: Frontend Workspace And Shell

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `apps/web/package.json`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/src/app-label.ts`
- Create: `apps/web/src/__tests__/app-label.test.ts`

- [x] Add pnpm workspace scripts for web lint, typecheck, test, and build.
- [x] Add a minimal Next.js app shell with search input, search button, AI search button, and product/deal/auction tabs.
- [x] Add a Vitest smoke test for the initial tab contract.
- [x] Verify with `pnpm --filter @dealmoa/web lint`, `typecheck`, `test`, and `build`.

### Task 3: Local Runtime And CI

**Files:**
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `infra/elasticsearch/Dockerfile`
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `.github/workflows/ci.yml`

- [x] Document local runtime variables without committed secrets.
- [x] Add Docker Compose `core` profile for web, api, PostgreSQL, Redis, and Elasticsearch with Nori.
- [x] Add GitHub Actions jobs for API and Web checks.
- [x] Verify compose syntax with `docker compose --profile core config`.
