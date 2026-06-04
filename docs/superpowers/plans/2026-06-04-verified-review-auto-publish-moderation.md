# Verified Review Auto Publish Moderation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change purchase verified reviews from every-review admin approval to MVP auto-publish with post-publication moderation.

**Architecture:** Normal receipt/order-history review submissions publish immediately as `approved` after request validation, without spending AI-review quota or calling the AI provider. Admin moderation remains available through the existing verified-review admin route by adding `hide` and `restore` actions; public product detail continues to show only `approved` reviews and keeps proof/AI/admin metadata private.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Next.js, React, TypeScript, Vitest.

---

## File Structure

- Modify `AGENTS.md`
  - Split user offer submission policy from verified purchase review policy.
- Modify `docs/planning.md`
  - Update the product policy to receipt/order-history based auto-publish plus post-publication moderation.
- Modify `docs/price-reviews.md`
  - Rewrite the verified-review lifecycle and admin moderation contract.
- Modify `docs/security-abuse.md`
  - Keep offer submissions pre-publication, move verified reviews to validation/rate-limit/post-moderation.
- Modify `docs/ai-assistant.md`
  - State that AI review is not called for every normal verified review.
- Modify `docs/handoff.md`
  - Record the new current policy and implementation result.
- Modify `apps/api/app/modules/evidence/schemas.py`
  - Require `proofReference`, add `hidden`, `hide`, and `restore` review literals.
- Modify `apps/api/app/modules/evidence/use_cases.py`
  - Create normal verified reviews as `approved`; add hide/restore moderation transitions.
- Modify `apps/api/app/modules/evidence/repository.py`
  - Existing approved-only public listing stays unchanged.
- Modify `apps/api/tests/test_evidence_api.py`
  - Update API tests for auto-publish, no AI call/quota use, proof required, hide/restore.
- Modify `apps/web/src/details/ProductDetailPage.tsx`
  - Change submit message and require proof reference before enabling submit.
- Modify `apps/web/src/details/api.ts`
  - Send trimmed proof reference as a required string.
- Modify `apps/web/src/details/types.ts`
  - Add `hidden` status.
- Modify `apps/web/src/details/__tests__/DetailPages.test.tsx`
  - Expect immediate public rendering after successful review submit.
- Modify `apps/web/src/me/MyPage.tsx`
  - Add `hidden` label.
- Modify `apps/web/src/me/__tests__/MyPage.test.tsx`
  - Add/adjust hidden status expectations.

## Task 1: API RED Tests

- [x] **Step 1: Update the main verified-review API test**

In `apps/api/tests/test_evidence_api.py`, replace the old admin-approval test with one that:

- posts a verified review as an authenticated user;
- expects `status == "approved"`;
- expects `aiDecision`, `aiReason`, and `aiReviewedAt` to be `null`;
- reads `GET /api/v1/products/{product_id}/verified-reviews`;
- expects the created review to be public immediately;
- asserts public response still excludes `userId`, `proofReference`, `aiReason`, and `resolutionNote`.

- [x] **Step 2: Add no-AI/no-quota test**

Add a use-case test where a provider raises if `review_verified_review` is called and an AI rate limiter has a limit of `1`. Create two verified reviews and assert:

- both are `approved`;
- no `AIReviewUsageEvent` rows exist;
- no `AIReviewRateLimitExceededException` is raised.

- [x] **Step 3: Add proof-required test**

Add an API test that posts a verified review with blank or missing `proofReference` and expects HTTP 422.

- [x] **Step 4: Add admin hide/restore test**

Create an approved review, call:

```http
PATCH /api/v1/admin/verified-reviews/{review_id}
{"action": "hide", "resolutionNote": "신고 확인"}
```

Then assert public product reviews no longer include it. Call:

```http
PATCH /api/v1/admin/verified-reviews/{review_id}
{"action": "restore", "resolutionNote": "오해 소명"}
```

Then assert the review is public again.

- [x] **Step 5: Run API RED command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_evidence_api.py -q
```

Expected: fail because verified reviews still start as `pending_review`, AI is still called, and `hide`/`restore` are not supported.

## Task 2: API Implementation

- [x] **Step 1: Update schemas**

Change:

```python
ReviewStatus = Literal["pending_review", "approved", "rejected", "hidden"]
ReviewAction = Literal["approve", "reject", "hide", "restore"]
```

Make `proof_reference` required:

```python
class VerifiedReviewCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=4000)
    proof_type: str = Field(alias="proofType", min_length=1, max_length=80)
    proof_reference: str = Field(alias="proofReference", min_length=1, max_length=255)
```

- [x] **Step 2: Auto-publish normal verified reviews**

In `EvidenceUseCases.create_verified_review`, remove the verified-review AI limiter/provider call from the normal path. Set:

```python
status="approved"
ai_decision=None
ai_reason=None
ai_reviewed_at=None
```

After persistence, call `domain_events.record_review_verified(review)` when `domain_events` exists.

- [x] **Step 3: Add hide/restore moderation transitions**

In `review_verified_review`:

- `approve`: only `pending_review -> approved`;
- `reject`: only `pending_review -> rejected`;
- `hide`: only `approved -> hidden`;
- `restore`: only `hidden -> approved`.

Write `admin_audit_logs` with actions:

- `verified_review.approved`
- `verified_review.rejected`
- `verified_review.hidden`
- `verified_review.restored`

Emit `review.verified` when the final status is `approved`.

- [x] **Step 4: Run API GREEN command**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_evidence_api.py -q
```

Expected: pass.

## Task 3: Web RED Tests

- [x] **Step 1: Update product detail submit test**

In `apps/web/src/details/__tests__/DetailPages.test.tsx`, make the POST response return `status: "approved"` and expect:

- message `인증 후기가 공개되었습니다.`;
- the submitted review title/body appears in the visible review list without admin approval.

- [x] **Step 2: Update type/status expectations**

Allow `hidden` status in `apps/web/src/details/types.ts` and My Page tests. Expect the My Page label for hidden reviews to be `숨김`.

- [x] **Step 3: Run Web RED command**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/details/__tests__/DetailPages.test.tsx src/me/__tests__/MyPage.test.tsx
```

Expected: fail until the UI message, submit behavior, and status labels are updated.

## Task 4: Web Implementation

- [x] **Step 1: Require proof reference in the form**

Disable the submit button when `proofReference.trim()` is empty.

- [x] **Step 2: Update submit API payload**

Send `proofReference: request.proofReference.trim()` instead of `null` fallback.

- [x] **Step 3: Update submit message**

Show:

```text
인증 후기가 공개되었습니다.
```

- [x] **Step 4: Add hidden status label**

Add `hidden: "숨김"` to My Page review status labels.

- [x] **Step 5: Run Web GREEN command**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/details/__tests__/DetailPages.test.tsx src/me/__tests__/MyPage.test.tsx
```

Expected: pass.

## Task 5: Docs, Security Review, Verification, Integration

- [x] **Step 1: Finish docs**

Update `docs/price-reviews.md`, `docs/security-abuse.md`, `docs/ai-assistant.md`, and `docs/handoff.md` so the current policy is consistent:

- offer submissions remain pre-publication review;
- verified purchase reviews auto-publish after lightweight validation;
- only suspicious/reported/admin-flagged reviews use moderation;
- AI is not called for every normal verified review;
- public responses never expose proof/AI/admin fields.

- [x] **Step 2: Security review**

Check:

- public review list filters `status == "approved"`;
- hidden reviews disappear from public product detail;
- proof reference remains private;
- AI/admin fields remain private;
- normal review creation does not call external AI provider.

- [x] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
git diff --check
```

- [ ] **Step 4: Commit and integrate**

Commit, push `feature/verified-review-auto-publish-moderation`, open PR to `develop`, wait for CI, merge if green, sync local `develop`, and write a Notion work log.

## Self-Review

- Spec coverage: user-requested policy change maps to docs, API behavior, admin moderation, Web copy, tests, and security review.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: `hidden` is added consistently to API review status and Web review status.
