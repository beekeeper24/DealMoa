# Product REST Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first REST API baseline for Product-centered DealMoa data.

**Architecture:** Keep routers thin and route through use cases, repositories, and domain exceptions. Add one SQLAlchemy session dependency as the transaction boundary, and wire global exception handlers so business errors use the project error shape.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0 Session, pytest TestClient, SQLite in-memory tests.

---

### Task 1: API Contract Tests

**Files:**
- Create: `apps/api/tests/test_product_api.py`

- [x] Write tests for creating/listing/getting products.
- [x] Write tests for creating/listing deals and auctions under a product.
- [x] Write tests that missing products return `PRODUCT_NOT_FOUND` in the common error shape.
- [x] Run the tests and verify they fail because routes do not exist.

### Task 2: API Infrastructure

**Files:**
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/core/exceptions.py`
- Create: `apps/api/app/core/exception_handlers.py`
- Modify: `apps/api/app/main.py`

- [x] Add `get_session()` with commit/rollback/close behavior.
- [x] Add `DealMoaException`, `ErrorCode`, and `ProductNotFoundException`.
- [x] Register global exception handlers for project exceptions and validation errors.

### Task 3: Product REST Module

**Files:**
- Create: `apps/api/app/modules/products/schemas.py`
- Create: `apps/api/app/modules/products/repository.py`
- Create: `apps/api/app/modules/products/use_cases.py`
- Create: `apps/api/app/modules/products/router.py`
- Modify: `apps/api/app/api/v1/router.py`

- [x] Add Pydantic request/response schemas.
- [x] Add repository methods for create/list/get product and create/list deal/auction.
- [x] Add use cases that raise domain exceptions instead of `HTTPException`.
- [x] Wire routes under `/api/v1/products`.

### Task 4: Verification And PR

- [x] Run focused API tests, then full API lint/typecheck/tests.
- [x] Run existing web checks because CI still gates both jobs.
- [x] Commit, push, open PR into `develop`, wait for CI, and merge if green.
