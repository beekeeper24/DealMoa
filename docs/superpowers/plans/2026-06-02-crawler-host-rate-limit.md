# Crawler Host Rate Limit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first per-host live crawler cap so one task run cannot fetch too many URLs from the same source host.

**Architecture:** Keep this as a worker-side per-task-run limiter. It is not a distributed Redis limiter yet. The live crawler still checks source allow before fetch; after source allow, it checks the host run cap and skips over-limit URLs before HTTP fetch, parser selection, submission validation, or DB writes.

**Tech Stack:** Python 3.12, Celery worker, Pydantic Settings, pytest, ruff, mypy.

---

## Tasks

- [x] Add `CRAWLER_MAX_URLS_PER_HOST` to worker settings, `.env.example`, and Docker Compose.
- [x] Add `CrawlerHostRunLimiter` unit tests and implementation.
- [x] Add live crawler task test proving over-limit URLs are skipped before fetch.
- [x] Wire limiter into `execute_live_crawler` after source allow and before fetch.
- [x] Document the per-run cap and deferred distributed/rate-window behavior.
- [x] Run worker tests, ruff, mypy, full Python tests, Docker config, web checks, and `git diff --check`.
- [ ] Commit, push, PR to `develop`, wait for CI, merge, sync local `develop`, and write Notion log.

## Acceptance Criteria

- Default `CRAWLER_MAX_URLS_PER_HOST` is `20`.
- Same-host URLs over the configured cap are skipped with `host_rate_limited`.
- Over-limit URLs are not fetched.
- Different hosts have independent counters.
- Source-denied URLs are skipped by source policy and do not need a rate-limit count.
- Existing no-live-fetch default behavior remains unchanged.
- This slice does not add Redis/global rate windows or production scheduling.
