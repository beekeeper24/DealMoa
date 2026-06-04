# Verified Review Submit Guards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block duplicate verified-review submissions before they auto-publish.

**Architecture:** Keep normal verified reviews auto-published, but reject duplicate submission attempts with stable domain exceptions. Add database unique constraints as storage-level guardrails and keep deterministic risk signals for text/spam prioritization only.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, pytest, existing Next.js admin UI contracts.

---

### Task 1: Backend RED Tests

**Files:**
- Modify: `apps/api/tests/test_evidence_api.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`

- [x] Add failing API test: same user cannot create a second verified review for the same product.
- [x] Add failing API test: a reused `proofReference` is rejected even from another user/product.
- [x] Assert both failures return HTTP 409 with stable codes and structured details.
- [x] Add failing Alembic assertions for unique constraints on `(user_id, product_id)` and `proof_reference`.

### Task 2: Backend Implementation

**Files:**
- Modify: `apps/api/app/core/exceptions.py`
- Modify: `apps/api/app/modules/evidence/models.py`
- Modify: `apps/api/app/modules/evidence/repository.py`
- Modify: `apps/api/app/modules/evidence/risk_analysis.py`
- Modify: `apps/api/app/modules/evidence/use_cases.py`
- Create: `apps/api/alembic/versions/20260605_0019_verified_review_submit_guards.py`

- [x] Add `VERIFIED_REVIEW_ALREADY_EXISTS` and `VERIFIED_REVIEW_PROOF_ALREADY_USED`.
- [x] Raise these exceptions before creating a verified review.
- [x] Add database unique constraints for same user/product and proof reference.
- [x] Remove duplicate proof/user-product inputs from normal risk analysis, since they are now blocked before creation.
- [x] Re-run focused backend tests until green.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/price-reviews.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/api-error-handling.md`
- Modify: `docs/product-api.md`
- Modify: `docs/handoff.md`
- Modify: `docs/superpowers/plans/2026-06-05-verified-review-risk-signals.md` if needed.

- [x] Document duplicate submission behavior and error codes.
- [x] Run backend and web full verification.
- [x] Run focused security review for duplicate defense and public data exposure.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync `develop`, and create Notion work log.
