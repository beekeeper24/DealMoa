# Verified Review Risk Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic platform-risk signals for auto-published verified purchase reviews so admins can prioritize post-publication moderation.

**Architecture:** Store risk fields on `verified_reviews`, compute them synchronously during review creation, and expose them only through admin verified-review responses. Public product detail remains proof/risk/moderation-safe, and normal reviews still auto-publish.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, Next.js, TypeScript, Vitest.

---

### Task 1: Backend TDD

**Files:**
- Modify: `apps/api/tests/test_evidence_api.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`

- [x] Add failing API tests that:
  - clean verified reviews store `riskLevel = low`, `riskScore = 0`, `riskReasons = []` in admin API responses;
  - off-platform contact, repeated URL, and blocked spam text produce risk reasons without auto-hiding;
  - admin verified-review queue orders higher-risk reviews before clean reviews;
  - public product verified-review responses still exclude `riskLevel`, `riskScore`, and `riskReasons`.
- [x] Add failing Alembic assertions for the new verified-review risk columns and status/risk index.

### Task 2: Backend Implementation

**Files:**
- Create: `apps/api/app/modules/evidence/risk_analysis.py`
- Create: `apps/api/alembic/versions/20260605_0018_verified_review_risk_signals.py`
- Modify: `apps/api/app/modules/evidence/models.py`
- Modify: `apps/api/app/modules/evidence/repository.py`
- Modify: `apps/api/app/modules/evidence/schemas.py`
- Modify: `apps/api/app/modules/evidence/router.py`
- Modify: `apps/api/app/modules/evidence/use_cases.py`

- [x] Add `moderation_risk_score`, `moderation_risk_level`, and `moderation_risk_reasons_json` columns with defaults.
- [x] Add deterministic risk analysis:
  - `external_contact`, `repeated_url`, and `blocked_commercial_spam` for obvious review spam text.
- [x] Keep all risky reviews `approved` on create; risk is an admin priority signal only.
- [x] Sort admin list by `moderation_risk_score desc`, then `created_at desc`, then `id desc`.
- [x] Use an admin-only response schema for risk fields so public product detail and user history do not gain internal risk metadata.

### Task 3: Web TDD And Implementation

**Files:**
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/__tests__/api.test.ts`
- Modify: `apps/web/src/admin/__tests__/AdminVerifiedReviewModerationPage.test.tsx`
- Modify: `apps/web/src/admin/AdminVerifiedReviewModerationPage.tsx`

- [x] Add failing web API/type/UI tests for `riskScore`, `riskLevel`, and `riskReasons`.
- [x] Render risk badge and reasons on the admin verified-review card.
- [x] Keep consumer report controls absent.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/price-reviews.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`
- Modify: `docs/planning.md` if needed.

- [x] Document that deterministic risk signals are admin priority only and do not auto-hide reviews.
- [x] Run focused backend and web tests.
- [x] Run full backend/web verification, diff check, and focused security review.
- [ ] Commit, push, PR to `develop`, wait for CI, merge, sync `develop`, and update Notion work log.
