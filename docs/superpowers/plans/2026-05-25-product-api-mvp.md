# Product API MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mature the Product/Deal/Auction REST baseline into a coherent Product API MVP slice.

**Architecture:** Keep work on `feature/product-api-mvp` and accumulate checkpoint commits. Do not open a PR until the slice is ready for `develop` integration or the user explicitly asks.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, pytest, uv, pnpm.

---

### Task 1: Cursor Pagination And Use Case Tests

**Files:**
- Modify: `apps/api/tests/test_product_api.py`
- Create: `apps/api/tests/test_product_use_cases.py`
- Modify: `apps/api/app/core/exceptions.py`
- Modify: `apps/api/app/modules/products/repository.py`
- Modify: `apps/api/app/modules/products/schemas.py`
- Modify: `apps/api/app/modules/products/use_cases.py`
- Modify: `apps/api/app/modules/products/router.py`

- [x] Write API tests for `limit`, `cursor`, `nextCursor`, invalid cursor, and validation errors.
- [x] Write use case tests for missing product and invalid cursor behavior.
- [x] Run focused tests and verify RED.
- [x] Implement pagination, cursor validation, and response shape.
- [x] Run focused tests and verify GREEN.

### Task 2: REST Quality Follow-Ups

**Files:**
- Modify API module files as needed.
- Test under `apps/api/tests/`.

- [x] Add `DEAL_NOT_FOUND` and `AUCTION_NOT_FOUND` when single-resource routes are introduced.
- [ ] Add cursor pagination to future search/list endpoints consistently.
- [ ] Keep repository/use case tests focused on business behavior, not FastAPI wiring.

### Task 3: Checkpoint Commit

- [x] Run API ruff, mypy, pytest.
- [x] Run Web lint, typecheck, test, build because CI gates both jobs.
- [x] Verify PostgreSQL runtime with Docker Compose, Alembic `upgrade head`, and HTTP create/list smoke checks.
- [x] Commit Korean checkpoint messages on `feature/product-api-mvp`.
- [x] Push the branch for backup/shared visibility.
- [ ] Do not open a PR yet.
