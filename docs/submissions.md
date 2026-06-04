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

`sourceUrl` must be an `http` or `https` URL. API intake rejects non-web schemes. Worker
crawler ingestion also applies configured source profile checks before network fetches or
database writes.

## Crawler Ingestion

`dealmoa.crawl_hot_deals_mock` is the first crawler ingestion boundary. It uses
deterministic mock crawled items and writes them into the same `submissions` table through
the existing submission intake use case.

`dealmoa.crawl_live_urls` is the first live HTTP crawler boundary. It is disabled by
default because `CRAWLER_LIVE_URLS` is empty. When URLs are configured, the worker checks
the URL host against `CRAWLER_SOURCE_PROFILES` before HTTP access, applies SSRF-safe
DNS/IP checks, respects robots.txt, rejects non-HTML or over-limit responses, and parses
only bounded HTML through the source parser configured by `CRAWLER_SOURCE_PARSERS`.
The current supported parser ID is `dealmoa_article`.
`CRAWLER_MAX_URLS_PER_HOST` limits how many URLs from the same host one task run may fetch.

Crawler tasks:

- creates or reuses a non-admin crawler system user;
- accepts only source hosts allowed by `CRAWLER_SOURCE_PROFILES`;
- parses live HTML only with a parser configured for the source host;
- skips unknown or blocked source hosts before network fetch or database writes;
- skips same-host URLs over `CRAWLER_MAX_URLS_PER_HOST` before network fetch;
- skips live fetched pages with missing or unsupported source parser configuration before
  submission validation or database writes;
- stores deal/auction candidates as `pending_review`;
- records the same mock AI first-pass result used by user submissions;
- relies on `sourceUrl` idempotency so repeated runs do not create duplicates;
- records completed and failed task summaries in `crawler_run_logs` for admin-only review;
- returns scanned, fetched, accepted, created, duplicate, skipped, and skip-reason counts
  where applicable.

Crawler ingestion does not publish Product/Deal/Auction rows or bypass admin approval.
Crawler run logs are operational summaries only; they do not store fetched HTML. Failed
run logs store an exception type and a bounded, redacted error message.

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
- Real source-specific parser implementations beyond the current bounded test parser.
- Retry metadata, production scheduling, and manual crawler controls.
- Edit/resubmit flow for rejected submissions.
