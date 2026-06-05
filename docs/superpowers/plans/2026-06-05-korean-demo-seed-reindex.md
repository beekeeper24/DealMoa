# Korean Demo Seed And Reindex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable Korean demo seed flow so search/ranking APIs and JMeter baseline runs have meaningful local data.

**Architecture:** Keep demo data under the API app because Product, Deal, Auction, price snapshots, and search reindexing are API-owned source-of-truth concerns. The seed flow is idempotent by stable source URLs/model names, and optional reindexing calls the existing `SearchUseCases.rebuild_indexes()` rather than duplicating Elasticsearch logic.

**Tech Stack:** Python 3.12, SQLAlchemy, uv module execution, pytest, Elasticsearch reindex use case.

---

### Task 1: Demo Seed Data And Use Case

**Files:**
- Create: `apps/api/app/modules/demo_seed/__init__.py`
- Create: `apps/api/app/modules/demo_seed/data.py`
- Create: `apps/api/app/modules/demo_seed/use_cases.py`
- Test: `apps/api/tests/test_demo_seed.py`

- [x] Add focused tests for Korean product/deal/auction creation.
- [x] Add focused test that running seed twice does not duplicate products/deals/auctions.
- [x] Define stable Korean seed data with product names, categories, specs, deal titles, sellers, and auction titles.
- [x] Implement idempotent seed use case using existing SQLAlchemy models.

### Task 2: CLI And Optional Reindex

**Files:**
- Create: `apps/api/app/modules/demo_seed/cli.py`
- Test: `apps/api/tests/test_demo_seed.py`

- [x] Add test that CLI-level function can run seed only.
- [x] Add test that CLI-level function calls reindex only when requested.
- [x] Implement `python -m app.modules.demo_seed.cli --reindex`.
- [x] Return a small summary: created/reused product, deal, auction counts and reindexed counts when requested.

### Task 3: Docs And JMeter Link

**Files:**
- Modify: `docs/performance.md`
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`
- Modify: `infra/jmeter/README.md`

- [x] Document local execution through `uv run python -m app.modules.demo_seed.cli`.
- [x] Document Docker Compose execution through the API container.
- [x] Explain that JMeter numbers become meaningful after migrations, seed, and reindex.

### Task 4: Verification And Integration

**Files:**
- Modify this plan checklist as steps complete.

- [x] Run focused demo seed tests.
- [x] Run backend tests or meaningful smoke subset.
- [x] Run ruff and mypy.
- [x] Run frontend tests only if docs or generated outputs affect web behavior.
- [x] Run Docker Compose config checks if compose commands change.
- [x] Run `git diff --check`.
- [ ] Commit, push, open PR to `develop`, wait for checks, merge, sync local `develop`, and create a Notion work log.

## Acceptance Criteria

- Seed data uses Korean product names and descriptions/specs.
- Re-running the seed command does not create duplicates.
- Search reindex can be triggered after seed without introducing a new indexing path.
- Docs show the local order: migrate DB, seed Korean data, reindex, run JMeter.
