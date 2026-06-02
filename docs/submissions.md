# Submissions

User and crawler submissions are candidate deal or auction listings. They are never
published automatically. The API or worker stores the candidate, records a deterministic
mock AI first-pass review, and waits for an explicit admin decision.

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

## Crawler Ingestion

`dealmoa.crawl_hot_deals_mock` is the first crawler ingestion boundary. It uses
deterministic mock crawled items and writes them into the same `submissions` table through
the existing submission intake use case.

The task:

- creates or reuses a non-admin crawler system user;
- accepts only source hosts allowed by `CRAWLER_SOURCE_PROFILES`;
- skips unknown or blocked source hosts before writing to the database;
- stores deal/auction candidates as `pending_review`;
- records the same mock AI first-pass result used by user submissions;
- relies on `sourceUrl` idempotency so repeated runs do not create duplicates;
- returns scanned, accepted, created, duplicate, and skipped counts.

It does not fetch live external pages, publish Product/Deal/Auction rows, or bypass admin
approval.

## AI First Pass

Submission intake uses the shared AI review provider boundary. The local and CI default
is deterministic mock review:

```json
{
  "decision": "needs_admin_review",
  "reason": "mock review passed: admin approval required"
}
```

The mock result is stored on the submission row. It does not approve publishing and does
not create Product, Deal, or Auction rows.

When `AI_REVIEW_PROVIDER=openai`, the API calls the OpenAI review adapter through the
same port. Provider output can only populate `aiDecision` and `aiReason`; the submission
status remains `pending_review`, and invalid/provider-failure responses fall back to
`needs_admin_review`.

## Admin Queue API

Admins can list and review submissions:

```http
GET /api/v1/admin/submissions?status=pending_review&limit=20&cursor=...
GET /api/v1/admin/submissions/{submission_id}/product-matches
PATCH /api/v1/admin/submissions/{submission_id}
```

Product match responses are read-only admin hints:

```json
{
  "items": [
    {
      "productId": "product-1",
      "name": "Galaxy S26 Ultra",
      "brand": "Samsung",
      "modelName": "SM-S260",
      "category": "smartphone",
      "score": 95,
      "matchedReasons": ["model", "brand", "category", "name"]
    }
  ]
}
```

Review request:

```json
{
  "action": "approve",
  "targetProductId": "product-1",
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

Approval creates a Product plus either a Deal or Auction by default. If `targetProductId`
is provided, approval attaches only the new Deal/Auction to the existing Product. In both
paths the API records the published IDs on the submission, writes an `admin_audit_logs`
row, and emits the existing `product.updated` plus `deal.created` or `auction.created`
outbox events.

Rejection only updates the submission status/resolution fields and writes an
`admin_audit_logs` row. It does not create Product, Deal, Auction, search documents, or
ranking signals.

## Web Entry Points

- `/submit`: authenticated user submission form.
- `/me`: authenticated user contribution history for own submissions.
- `/admin/submissions`: admin submission review queue.
- Search header always links to `/submit`.
- Authenticated search sessions also link to `/me`.
- Admin sessions see both report review and submission review links.
- The My Page history uses only `GET /me/submissions` and shows status, review notes,
  source links, and published Product/Deal/Auction links when available.
- The admin submission queue shows product match candidates and lets admins approve into
  an existing Product or publish as a new Product.

## Deferred

- Real AI provider integration.
- Server-side rate limit storage.
- URL allowlist/blocklist and suspicious-link scoring beyond the current `http/https`
  scheme check.
- Product merge UI and background duplicate cleanup.
- Real crawler integration and source-specific parsing.
- Edit/resubmit flow for rejected submissions.
