# API Prometheus Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose basic FastAPI request metrics through a Prometheus-compatible `/metrics` endpoint.

**Architecture:** Add an API-local metrics module that owns Prometheus counters, histograms, middleware, and the `/metrics` response. Register the middleware in `create_app()` before routers are included. Use route templates for path labels so `/products/{product_id}` does not explode label cardinality.

**Tech Stack:** FastAPI, Starlette middleware, prometheus-client, pytest, uv workspace.

---

### Task 1: RED Metrics Tests

**Files:**
- Create: `apps/api/tests/test_metrics.py`

- [x] Add a failing test that `GET /metrics` returns `text/plain` Prometheus output.
- [x] Add a failing test that requests to `/health`, `/api/v1/health`, and a missing route increment `dealmoa_api_http_requests_total`.
- [x] Add a failing test that dynamic route labels use templates such as `/api/v1/products/{product_id}` instead of concrete ids.
- [x] Add a failing test that `/metrics` scrape requests are excluded from request counters.
- [x] Run focused tests and confirm failure because `/metrics` does not exist yet.

### Task 2: Metrics Implementation

**Files:**
- Create: `apps/api/app/core/metrics.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/pyproject.toml`
- Modify: `uv.lock`

- [x] Add `prometheus-client` dependency.
- [x] Define `dealmoa_api_http_requests_total` counter with `method`, `path`, and `status_code` labels.
- [x] Define `dealmoa_api_http_request_duration_seconds` histogram with `method` and `path` labels.
- [x] Implement middleware that records successful, handled-error, and unhandled-error requests.
- [x] Exclude `/metrics` from request metrics.
- [x] Add root-level `GET /metrics` returning `generate_latest()` with `CONTENT_TYPE_LATEST`.
- [x] Run focused tests and confirm pass.

### Task 3: Docs, Verification, PR

**Files:**
- Modify: `docs/observability.md`
- Modify: `docs/handoff.md`

- [x] Document `/metrics`, metric names, labels, and current non-goals.
- [x] Run backend full tests, mypy, ruff.
- [x] Run `git diff --check`.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync `develop`, and create Notion work log.
