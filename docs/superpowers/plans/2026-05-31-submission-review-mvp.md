# Submission Review MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for model, state transition, auth, and approval behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user offer submissions with mock AI first-pass review and admin approval/rejection.

**Architecture:** Add a `submissions` API module as the source of truth for user-submitted deal/auction candidates. Submission intake stores raw candidate data and a deterministic mock AI review result, but never publishes content. Admin approval creates the Product plus Deal/Auction only after an explicit admin decision, using existing product use-case paths and domain events.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js, React, TypeScript, Tailwind CSS.

---

## Scope

- Authenticated users can submit deal or auction candidates.
- Duplicate `sourceUrl` returns the existing submission instead of creating another row.
- Mock AI review stores `aiDecision`, `aiReason`, and `aiReviewedAt`.
- Admins can list pending submissions.
- Admins can approve or reject a submission.
- Approval creates a Product and either a Deal or Auction.
- Rejection records an admin reason and does not create Product/Deal/Auction rows.
- Web adds a user submission form and admin submission queue entry point.

## Non-goals

- No automatic publishing before admin approval.
- No real AI provider call.
- No production-grade rate-limit store in this slice.
- No product matching/merge workflow; approval creates a new Product for MVP.
- No crawler integration.

## API Contract

```http
POST /api/v1/submissions
GET /api/v1/me/submissions
GET /api/v1/admin/submissions?status=pending_review
PATCH /api/v1/admin/submissions/{submission_id}
```

Submission statuses:

- `pending_review`: created and AI mock reviewed, awaiting admin.
- `approved`: admin approved and published.
- `rejected`: admin rejected.

Admin actions:

- `approve`
- `reject`

## Verification

- API focused tests for model, use case, router, migration.
- Worker task test for stable AI mock review payload.
- Web tests for submission form and admin queue.
- Playwright smoke for submission form and admin approval with mocked APIs.
- Full local API/Web lint, typecheck, tests, build, and e2e before PR.
