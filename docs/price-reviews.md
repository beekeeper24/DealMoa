# Price History And Verified Reviews

## Scope

This document covers the first MVP foundation for product evidence:

- price history snapshots attached to a product;
- authenticated verified review submission;
- mock AI first-pass review;
- admin approval or rejection;
- public display of approved verified reviews only.

Receipt upload, OCR, real AI provider integration, review scoring impact, product
discussion, and My Page review history remain deferred.

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

The MVP records a deterministic mock AI review result:

```text
decision = needs_admin_review
reason = mock review passed: receipt proof requires admin approval
```

The review always starts as `pending_review`. AI output is evidence for the
admin queue only; it never publishes the review by itself.

## Admin Review

Admin routes:

```http
GET /api/v1/admin/verified-reviews?status=pending_review
PATCH /api/v1/admin/verified-reviews/{review_id}
```

Patch request:

```json
{
  "action": "approve",
  "resolutionNote": "영수증 확인"
}
```

Rules:

- only `ADMIN` users can list or review pending verified reviews;
- only `pending_review` rows can be approved or rejected;
- approval/rejection writes `admin_audit_logs`;
- approval writes a `review.verified` transactional outbox event.

## Public Display Boundary

Public product detail reads approved reviews only:

```http
GET /api/v1/products/{product_id}/verified-reviews
```

The public response intentionally excludes internal user ids, proof references,
AI review text, admin reviewer ids, and resolution notes:

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

The admin and creation responses still include proof and review metadata because
those paths are authenticated and need the data for moderation.
