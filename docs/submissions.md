# Submissions

User submissions are candidate deal or auction listings. They are never published
automatically. The API stores the candidate, records a deterministic mock AI first-pass
review, and waits for an explicit admin decision.

## User API

Authenticated users can create submissions:

```http
POST /api/v1/submissions
GET /api/v1/me/submissions?limit=20&cursor=...
```

Create request:

```json
{
  "offerType": "deal",
  "sourceUrl": "https://example.com/deals/galaxy-s26",
  "productName": "Galaxy S26",
  "brand": "Samsung",
  "modelName": "SM-S260",
  "category": "smartphone",
  "title": "Galaxy S26 launch deal",
  "seller": "Example Store",
  "originalPrice": 1400000,
  "salePrice": 1090000,
  "currentPrice": null,
  "currency": "KRW",
  "description": "Launch discount"
}
```

Allowed `offerType` values are `deal` and `auction`. Deal submissions require
`salePrice`; auction submissions require `currentPrice`.

Duplicate `sourceUrl` submissions return the existing row instead of creating a second
queue item. This keeps the first MVP idempotent by source URL. Later duplicate detection
can add normalized URL and product-matching rules.

`sourceUrl` must be an `http` or `https` URL. Allowlist/blocklist and source reputation
checks are deferred, but non-web schemes are rejected at intake.

## AI First Pass

The current AI review is a mock boundary:

```json
{
  "decision": "needs_admin_review",
  "reason": "mock review passed: admin approval required"
}
```

The mock result is stored on the submission row. It does not approve publishing and does
not create Product, Deal, or Auction rows.

## Admin Queue API

Admins can list and review submissions:

```http
GET /api/v1/admin/submissions?status=pending_review&limit=20&cursor=...
PATCH /api/v1/admin/submissions/{submission_id}
```

Review request:

```json
{
  "action": "approve",
  "resolutionNote": "Approved for MVP seed data"
}
```

Allowed review actions:

- `approve`
- `reject`

Allowed statuses:

- `pending_review`
- `approved`
- `rejected`

Approval creates a Product plus either a Deal or Auction in the same transaction, records
the published IDs on the submission, writes an `admin_audit_logs` row, and emits the
existing `product.updated` plus `deal.created` or `auction.created` outbox events.

Rejection only updates the submission status/resolution fields and writes an
`admin_audit_logs` row. It does not create Product, Deal, Auction, search documents, or
ranking signals.

## Web Entry Points

- `/submit`: authenticated user submission form.
- `/admin/submissions`: admin submission review queue.
- Search header always links to `/submit`.
- Admin sessions see both report review and submission review links.

## Deferred

- Real AI provider integration.
- Server-side rate limit storage.
- URL allowlist/blocklist and suspicious-link scoring beyond the current `http/https`
  scheme check.
- Product matching/merge suggestions before approval.
- Crawler integration.
- Dedicated user "my submissions" page.
