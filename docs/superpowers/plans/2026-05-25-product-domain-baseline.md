# Product Domain Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first PostgreSQL-backed Product, Deal, and Auction schema baseline for DealMoa.

**Architecture:** Keep this PR below the REST boundary: SQLAlchemy model metadata, Alembic migration, and tests only. Product remains the stable identity; deals and auctions attach to products with explicit foreign keys so search, ranking, and ingestion can build on the same source-of-truth tables.

**Tech Stack:** FastAPI project layout, SQLAlchemy 2.0, Alembic, pytest, uv, PostgreSQL-compatible schema with SQLite migration smoke tests.

---

### Task 1: SQLAlchemy Base And Product Models

**Files:**
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/modules/products/models.py`
- Create: `apps/api/app/modules/products/__init__.py`
- Test: `apps/api/tests/test_product_models.py`

- [x] Write tests that define the required `products`, `deals`, and `auctions` table contract.
- [x] Run the tests and verify they fail because the model modules do not exist.
- [x] Implement SQLAlchemy metadata and models for Product, Deal, and Auction.
- [x] Run the focused model tests and verify they pass.

### Task 2: Alembic Migration Baseline

**Files:**
- Create: `apps/api/alembic.ini`
- Create: `apps/api/alembic/env.py`
- Create: `apps/api/alembic/versions/20260525_0001_product_deal_auction_baseline.py`
- Test: `apps/api/tests/test_alembic_migrations.py`

- [x] Write an Alembic upgrade smoke test against a temporary SQLite database.
- [x] Run the test and verify it fails before Alembic config/migration exists.
- [x] Add Alembic config, metadata loading, and the baseline migration.
- [x] Run the focused migration test and verify it passes.

### Task 3: Verification And PR

**Files:**
- Modify: `apps/api/pyproject.toml`

- [x] Add any missing test/runtime dependency needed by migration tests.
- [x] Run API ruff, mypy, pytest.
- [x] Run git diff checks.
- [ ] Commit, push, open PR into `develop`, wait for CI, and merge if green.
