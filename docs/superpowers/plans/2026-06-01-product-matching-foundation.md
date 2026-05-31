# Product Matching Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for admin authorization, publishing state transitions, and product matching behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small deterministic product matching foundation so admin submission approval can attach a deal/auction to an existing Product instead of always creating a duplicate Product.

**Architecture:** Keep matching inside the submission review boundary for now. Product remains the stable identity. Matching suggestions are read-only candidates computed from existing Product rows. Admin approval may optionally specify a target Product id; publishing then creates only the offer under that Product.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Next.js, React, TypeScript.

---

## Scope

- Add deterministic product match candidate scoring for submissions.
- Add admin-only `GET /api/v1/admin/submissions/{submission_id}/product-matches`.
- Extend admin submission approval with optional `targetProductId`.
- Admin web submission queue shows suggested products and lets the admin approve into an existing product.
- Preserve current default: approving without `targetProductId` creates a new Product.

## Non-goals

- No real crawler implementation.
- No AI/vector matching.
- No automatic approval.
- No product merge UI.
- No background dedupe job.
- No Elasticsearch dependency for matching.

## Matching Rules

- Exact normalized model match is the strongest signal.
- Matching brand/category add confidence.
- Shared normalized product-name tokens add confidence.
- Suggestions are capped and sorted by score descending.
- Low-score candidates can still be shown as admin hints, but never auto-selected.

## API Contract

```http
GET /api/v1/admin/submissions/{submission_id}/product-matches
PATCH /api/v1/admin/submissions/{submission_id}
```

Approval request extension:

```json
{
  "action": "approve",
  "targetProductId": "existing-product-id",
  "resolutionNote": "기존 상품에 연결"
}
```

## Security Boundaries

- Match lookup is admin-only.
- Approval is still admin-only and only pending submissions can publish.
- A missing `targetProductId` raises `PRODUCT_NOT_FOUND`.
- Matching suggestions do not publish anything by themselves.
- External source URLs remain review data; matching does not fetch remote URLs.

## Verification

- API tests for admin-only suggestions, sorted match candidates, existing-product approval, and invalid target product.
- Web tests for suggestion rendering and `targetProductId` request body.
- Existing submission approval tests keep passing for new-product default.
- Focused cso review for admin authorization and external URL boundaries.

## Implementation Checklist

- [x] Add matching schemas and use-case behavior.
- [x] Add admin match API and API tests.
- [x] Extend approval request with `targetProductId`.
- [x] Add admin web matching UI and tests.
- [x] Update docs and run focused security review.
