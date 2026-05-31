# Product Discussion Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for auth, admin authorization, moderation state transitions, and user-generated content boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first product-scoped discussion foundation so product detail pages can host lightweight user discussion without turning community opinion into AI purchase-check fact.

**Architecture:** Add a `discussions` API module anchored to Product. Store immutable comment body plus a moderation `status`. Public product discussion reads visible comments only. Authenticated users can write comments. Admins can hide or restore comments with audit logs.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js, React, TypeScript, Tailwind CSS.

---

## Scope

- Add product discussion comments table.
- Add public `GET /api/v1/products/{product_id}/discussions`.
- Add authenticated `POST /api/v1/products/{product_id}/discussions`.
- Add admin `GET /api/v1/admin/discussions`.
- Add admin `PATCH /api/v1/admin/discussions/{comment_id}` to hide or restore a comment.
- Product detail shows visible discussion comments and an authenticated comment form.
- Admin moderation writes `admin_audit_logs`.

## Non-goals

- No nested replies.
- No voting, likes, or ranking impact.
- No notifications.
- No AI/community sentiment summarization.
- No edit/delete by author yet.
- No rich text or image upload.

## API Contract

```http
GET /api/v1/products/{product_id}/discussions
POST /api/v1/products/{product_id}/discussions
GET /api/v1/admin/discussions?status=visible
PATCH /api/v1/admin/discussions/{comment_id}
```

Comment statuses:

- `visible`: public on product detail.
- `hidden`: hidden by admin moderation.

Admin actions:

- `hide`
- `restore`

## Security Boundaries

- Discussion creation requires login.
- Public responses expose nickname, not email or proof/admin metadata.
- Comment text is rendered as plain React text, not HTML.
- Discussion content is not used as AI purchase-check evidence.
- Admin moderation changes visibility; report counts and comment counts do not change ranking.

## Verification

- API tests for auth, public visibility, admin-only moderation, audit logs, and not-found behavior.
- Migration tests for table/index/FK presence.
- Web API/component tests for product detail discussion rendering and authenticated submission.
- Focused security review for user-generated content handling.

## Implementation Checklist

- [x] Add discussion model and Alembic migration.
- [x] Add discussion schemas/repository/use cases/router.
- [x] Add API tests and migration assertions.
- [x] Add product detail discussion client/UI/tests.
- [x] Update docs and run focused security review.
