# Crawler Source Parser Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a source-specific parser selection boundary so live crawler HTML is parsed only by configured parser IDs for allowed source hosts.

**Architecture:** Keep parser selection inside `apps/worker`. `CRAWLER_SOURCE_PROFILES` continues to decide whether a source host may be fetched; new `CRAWLER_SOURCE_PARSERS` decides which parser may parse that host after fetch. Unsupported or missing parser configuration skips the item before `SubmissionCreateRequest` validation or DB writes.

**Tech Stack:** Python 3.12, Celery worker, Pydantic Settings, stdlib HTML parser, pytest, ruff, mypy.

---

## File Structure

- Modify: `apps/worker/worker_app/config.py`
  - Add `CRAWLER_SOURCE_PARSERS`.
- Modify: `.env.example`
  - Document the source parser mapping default.
- Modify: `docker-compose.yml`
  - Pass `CRAWLER_SOURCE_PARSERS` to worker and worker-beat.
- Modify: `apps/worker/worker_app/crawler_parsers.py`
  - Replace single parser function usage with `CrawlerParserRegistry`, `parse_source_parsers`, and parser IDs.
- Modify: `apps/worker/worker_app/tasks.py`
  - Use the parser registry in `execute_live_crawler`.
- Modify: `apps/worker/tests/test_crawler_parsers.py`
  - Cover parser mapping, configured parser success, unknown source skip, unsupported parser skip, and invalid config.
- Modify: `apps/worker/tests/test_tasks.py`
  - Cover live crawler skip reason when parser is not configured.
- Modify: `docs/async-events.md`, `docs/security-abuse.md`, `docs/submissions.md`, `docs/handoff.md`
  - Document parser mapping and remaining deferred source-specific parser implementation.

---

## Tasks

- [x] Add failing parser registry tests in `apps/worker/tests/test_crawler_parsers.py`.
- [x] Add failing live crawler task skip-reason test in `apps/worker/tests/test_tasks.py`.
- [x] Add `CRAWLER_SOURCE_PARSERS` to worker settings, `.env.example`, and Docker Compose.
- [x] Implement `CrawlerParserRegistry` and `parse_source_parsers`.
- [x] Wire `execute_live_crawler` to use the registry and return stable parser skip reasons.
- [x] Update async, security, submission, and handoff docs.
- [x] Run worker focused tests.
- [x] Run ruff, mypy, full Python tests, Docker Compose config, web verification, and `git diff --check`.
- [x] Commit, push, open PR to `develop`, wait for CI, merge, sync local `develop`, and create Notion work log.

## Acceptance Criteria

- `CRAWLER_SOURCE_PARSERS` defaults to `mock.example.com:dealmoa_article`.
- A live crawler URL with no parser mapping is skipped with `parser_not_configured`.
- A live crawler URL with an unsupported parser ID is skipped with `unsupported_source_parser`.
- A configured `dealmoa_article` parser still parses the existing `data-dealmoa-*` article format.
- Parser selection happens after safe fetch and before `SubmissionCreateRequest`/DB writes.
- Existing mock crawler behavior remains unchanged.
- Live crawler default remains no external fetch unless `CRAWLER_LIVE_URLS` is configured.

## Self-Review

- Spec coverage: This plan covers parser mapping, task skip reasons, docs, and full verification.
- Placeholder scan: No placeholders remain.
- Type consistency: Parser IDs use strings in config and return `CrawlerRawItem | None` from registry parsing.
