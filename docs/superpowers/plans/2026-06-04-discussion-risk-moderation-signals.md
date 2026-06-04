# Discussion Risk Moderation Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build issue #57 so product discussion comments get deterministic risk signals for admin prioritization without automatic hiding or deletion.

**Architecture:** Store moderation risk score, level, and reasons on `product_discussion_comments`. Analyze comment body synchronously during comment creation with a small deterministic rule analyzer. Public discussion responses keep risk fields hidden; admin discussion responses and `/admin/discussions` display them. Admin queue ordering prioritizes higher risk inside the selected visibility status.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js, React, TypeScript, Vitest, pytest.

---

## File Structure

- Create `apps/api/app/modules/discussions/risk_analysis.py`
  - Deterministic analyzer that returns score/level/reasons for blocked words, external-contact phrases, and repeated URLs.
- Modify `apps/api/app/modules/discussions/models.py`
  - Add `moderation_risk_score`, `moderation_risk_level`, and `moderation_risk_reasons_json`.
- Create `apps/api/alembic/versions/20260604_0016_discussion_moderation_risk.py`
  - Add risk columns with safe defaults and an admin queue index.
- Modify `apps/api/app/modules/discussions/use_cases.py`
  - Analyze body during `create_comment`; do not change `status`.
- Modify `apps/api/app/modules/discussions/repository.py`
  - Sort admin queue by `moderation_risk_score DESC`, then `created_at DESC`, then `id DESC`.
- Modify `apps/api/app/modules/discussions/schemas.py` and `router.py`
  - Expose risk fields only in `DiscussionCommentResponse`, not in public response.
- Modify `apps/api/tests/test_discussions_api.py`
  - Add tests for clean/risky comment creation, public field exclusion, and admin risk ordering.
- Modify `apps/api/tests/test_alembic_migrations.py`
  - Assert new columns and index exist.
- Modify `apps/web/src/admin/types.ts`
  - Add `riskLevel`, `riskScore`, and `riskReasons` to `AdminDiscussionComment`.
- Modify `apps/web/src/admin/AdminDiscussionModerationPage.tsx`
  - Render risk badge/reasons on admin cards.
- Modify `apps/web/src/admin/__tests__/AdminDiscussionModerationPage.test.tsx`
  - Assert risk badge/reason rendering.
- Modify `docs/discussions.md`, `docs/security-abuse.md`, and `docs/handoff.md`
  - Document automatic risk signals and non-goals.

## Task 1: API Red Tests

**Files:**
- Modify: `apps/api/tests/test_discussions_api.py`
- Modify: `apps/api/tests/test_alembic_migrations.py`

- [x] **Step 1: Add failing API tests**

Add tests that prove:

- clean comments remain `visible` with `riskLevel = "low"` and no reasons;
- risky comments remain `visible` but admin response includes `riskLevel = "high"` and reasons such as `external_contact` and `repeated_url`;
- public discussion response does not include `riskLevel`, `riskScore`, or `riskReasons`;
- admin discussion list orders high-risk comments before low-risk comments inside the same status.

- [x] **Step 2: Add failing migration assertions**

Assert `product_discussion_comments` has:

- `moderation_risk_score`
- `moderation_risk_level`
- `moderation_risk_reasons_json`
- `ix_product_discussion_comments_status_risk_created_at`

- [x] **Step 3: Run red tests**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_discussions_api.py apps/api/tests/test_alembic_migrations.py -q
```

Expected: fail because risk fields and migration do not exist.

## Task 2: API Implementation

**Files:**
- Create: `apps/api/app/modules/discussions/risk_analysis.py`
- Modify: `apps/api/app/modules/discussions/models.py`
- Create: `apps/api/alembic/versions/20260604_0016_discussion_moderation_risk.py`
- Modify: `apps/api/app/modules/discussions/use_cases.py`
- Modify: `apps/api/app/modules/discussions/repository.py`
- Modify: `apps/api/app/modules/discussions/schemas.py`
- Modify: `apps/api/app/modules/discussions/router.py`

- [x] **Step 1: Add risk analyzer**

Rules:

- `external_contact`: words such as `카톡`, `카카오톡`, `오픈채팅`, `텔레그램`, `telegram`, phone-like `010-0000-0000`;
- `repeated_url`: two or more `http://` or `https://` URLs;
- `blocked_commercial_spam`: phrases such as `무료바카라`, `사설토토`, `비밀링크`.

Score mapping:

- low: score `0`;
- medium: score `50`;
- high: score `100`.

- [x] **Step 2: Store risk fields on create**

Run analysis in `create_comment` and set the columns. Do not change `status`, even for high-risk comments.

- [x] **Step 3: Expose admin-only risk fields**

Add aliases:

- `riskScore`
- `riskLevel`
- `riskReasons`

Only `DiscussionCommentResponse` gets these fields.

- [x] **Step 4: Sort admin queue by risk priority**

Order by:

```text
moderation_risk_score DESC, created_at DESC, id DESC
```

Cursor logic must use the same order.

- [x] **Step 5: Run API green tests**

Run:

```bash
PYTHONPATH=apps/api uv run pytest apps/api/tests/test_discussions_api.py apps/api/tests/test_alembic_migrations.py -q
```

Expected: all selected API tests pass.

## Task 3: Web Red and Green

**Files:**
- Modify: `apps/web/src/admin/types.ts`
- Modify: `apps/web/src/admin/AdminDiscussionModerationPage.tsx`
- Modify: `apps/web/src/admin/__tests__/AdminDiscussionModerationPage.test.tsx`

- [x] **Step 1: Add failing Web test**

Update `discussionFixture` with risk fields and assert admin cards render:

- `high`
- `external_contact`
- `repeated_url`

- [x] **Step 2: Implement risk badge/reasons**

Render a compact badge near status/product id and reason chips under the body.

- [x] **Step 3: Run focused Web tests**

Run:

```bash
corepack pnpm --filter @dealmoa/web test -- src/admin/__tests__/AdminDiscussionModerationPage.test.tsx src/admin/__tests__/api.test.ts
```

Expected: selected Web tests pass.

## Task 4: Docs, Verification, and Security Review

**Files:**
- Modify: `docs/discussions.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Update docs**

Document:

- risk analysis is deterministic and advisory;
- risk never auto-hides, deletes, ranks, or penalizes users in this slice;
- public responses do not expose risk fields;
- admin queue uses risk only for review priority.

- [x] **Step 2: Run verification**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests/test_discussions_api.py apps/api/tests/test_alembic_migrations.py -q
uv run ruff check apps/api apps/consumer apps/worker
uv run mypy apps/api apps/consumer apps/worker
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
git diff --check
```

- [x] **Step 3: Focused security review**

Review the diff for:

- no automatic hide/delete;
- public risk field exclusion;
- admin-only risk display;
- no raw HTML rendering;
- deterministic rules only, no LLM/AI judgment.
