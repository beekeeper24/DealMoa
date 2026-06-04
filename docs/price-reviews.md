# Price History And Verified Reviews

## Scope

This document covers the first MVP foundation for product evidence:

- price history snapshots attached to a product;
- authenticated verified review submission;
- receipt/order-history proof reference validation;
- automatic public display for normal MVP verified reviews;
- post-publication admin moderation for suspicious, reported, or admin-flagged reviews.

Receipt image upload, OCR, automatic proof matching, suspicious-review AI escalation,
review scoring impact, and richer moderation queues remain deferred.

## Price History

Price history is stored as immutable snapshots. A snapshot records the product,
source type, source id, observed price, currency, and observed timestamp.

Current snapshot producers:

- deal creation records the deal sale price;
- auction creation records the initial auction current price;
- accepted auction bids record the updated auction current price.

Public route:

```http
GET /api/v1/products/{product_id}/price-history
```

The route uses cursor pagination and returns newest observations first:

```json
{
  "items": [
    {
      "id": "price-id",
      "productId": "product-id",
      "sourceType": "deal",
      "sourceId": "deal-id",
      "price": 1090000,
      "currency": "KRW",
      "observedAt": "2026-06-01T00:00:00Z",
      "createdAt": "2026-06-01T00:00:00Z"
    }
  ],
  "nextCursor": null
}
```

## Verified Review Submission

Submitting a verified review requires bearer auth:

```http
POST /api/v1/products/{product_id}/verified-reviews
```

Request:

```json
{
  "rating": 5,
  "title": "실구매 기준 만족",
  "body": "배송과 제품 상태 모두 좋았습니다.",
  "proofType": "receipt",
  "proofReference": "order-123"
}
```

Verified-review intake validates the text fields and requires a non-empty proof
reference. In the MVP this proof is an order number, receipt reference, or purchase
history reference string. Receipt upload/OCR and automatic proof matching come later.

Normal verified reviews publish immediately as `approved`. This keeps the UX close to
receipt-verified review products: users do not wait for a human to approve ordinary
reviews, and admins do not spend time on every normal review.

The AI review provider is not called for every normal verified-review submission. It is
reserved for future suspicious-review escalation, 신고 누적, or targeted abuse review.
This avoids unnecessary token spend and keeps admin attention on exceptional cases.

When `AI_REVIEW_PROVIDER=openai`, the adapter sends review text and proof metadata shape
to the provider, but not the raw `proofReference`. Provider output can only populate
`aiDecision` and `aiReason`; invalid/provider-failure responses fall back to
`needs_admin_review`. This provider boundary remains available for future escalation but
is not part of the normal auto-publish path.

Offer submissions still share the user-triggered AI review quota. Normal verified-review
submission does not consume that AI quota because it does not call the AI provider in the
MVP auto-publish path. Separate user/content rate limits for reviews can be added when
traffic requires them.

## My Review History

Authenticated users can list only their own verified-review submissions:

```http
GET /api/v1/me/verified-reviews?limit=20&cursor=...
```

The response uses the same `items` and `nextCursor` shape as other cursor-paginated
lists. It returns the owner's review status, AI first-pass reason, proof metadata, and
admin resolution fields so the user can understand review progress. The query is always
scoped to the current bearer-token user; it does not expose another user's reviews.

## Admin Moderation

Admin routes:

```http
GET /api/v1/admin/verified-reviews?status=approved
PATCH /api/v1/admin/verified-reviews/{review_id}
```

Patch request:

```json
{
  "action": "hide",
  "resolutionNote": "신고 확인"
}
```

Rules:

- only `ADMIN` users can list or moderate verified reviews;
- normal public reviews are `approved`;
- `hide` moves an approved review to `hidden`, removing it from public product detail;
- `restore` moves a hidden review back to `approved`;
- `approve` and `reject` remain for future suspicious-review `pending_review` rows;
- all moderation actions write `admin_audit_logs`;
- creation and restore/approval to public status write a `review.verified`
  transactional outbox event.

## Public Display Boundary

Public product detail reads `approved` reviews only:

```http
GET /api/v1/products/{product_id}/verified-reviews
```

The public response intentionally excludes internal user ids, proof references, AI review
text, admin reviewer ids, and resolution notes. `hidden`, `pending_review`, and
`rejected` reviews are not returned:

```json
{
  "items": [
    {
      "id": "review-id",
      "productId": "product-id",
      "rating": 5,
      "title": "실구매 기준 만족",
      "body": "배송과 제품 상태 모두 좋았습니다.",
      "createdAt": "2026-06-01T00:00:00Z",
      "updatedAt": "2026-06-01T00:05:00Z"
    }
  ],
  "nextCursor": null
}
```

The admin, creation, and My Page responses still include proof and moderation metadata
because those paths are authenticated and need the data for owner/admin context.
