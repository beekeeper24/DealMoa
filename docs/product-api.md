# Product API

## Scope

Product API MVP는 상품 중심 데이터의 최소 REST 계약이다. `Product`가 안정적인 상품 identity이고, `Deal`과 `Auction`은 각각 특정 상품에 연결된 offer/listing이다.

이번 범위는 PostgreSQL 원천 데이터와 API 계약을 고정하는 데 집중한다. 검색 색인과 검색 API는 `docs/search-ranking.md`의 Search API MVP에서 별도 slice로 다룬다. 즐겨찾기, 알림, 관리자 워크플로는 별도 slice로 다룬다.

## Routes

Base prefix는 `/api/v1`이다.

```http
POST /api/v1/products
GET /api/v1/products
GET /api/v1/products/{product_id}

POST /api/v1/products/{product_id}/deals
GET /api/v1/products/{product_id}/deals
GET /api/v1/deals/{deal_id}

POST /api/v1/products/{product_id}/auctions
GET /api/v1/products/{product_id}/auctions
GET /api/v1/auctions/{auction_id}
POST /api/v1/auctions/{auction_id}/bids
```

Routers stay thin: request validation happens through Pydantic schemas, business behavior goes through use cases, persistence goes through repositories, and business errors are raised as DealMoa domain exceptions.

## Web Detail MVP

The first web detail slice reuses the existing routes above rather than adding a
new aggregate detail endpoint:

- Product detail calls `GET /api/v1/products/{product_id}`,
  `GET /api/v1/products/{product_id}/deals`, and
  `GET /api/v1/products/{product_id}/auctions`.
- Deal detail calls `GET /api/v1/deals/{deal_id}` and then loads the linked
  product with `GET /api/v1/products/{product_id}`.
- Auction detail calls `GET /api/v1/auctions/{auction_id}` and then loads the
  linked product with `GET /api/v1/products/{product_id}`.
- Deal and auction detail pages use the existing report APIs from
  `docs/reports.md`.
- Auction detail uses `POST /api/v1/auctions/{auction_id}/bids`.

This keeps the MVP simple and demoable while price history, verified reviews,
discussion, and AI purchase checks are still deferred.

## Cursor Pagination

List endpoints use cursor pagination from the first Product API MVP slice.

Supported query parameters:

- `limit`: integer, `1..50`, default `20`.
- `cursor`: optional item id from the previous page's `nextCursor`.

List response shape:

```json
{
  "items": [],
  "nextCursor": null
}
```

Current ordering is newest first using `created_at DESC, id DESC`. When a page has more results, `nextCursor` is the last returned item's id. Clients pass that value as `cursor` to fetch the next page.

Invalid cursor behavior:

```json
{
  "error": {
    "code": "INVALID_SEARCH_CURSOR",
    "message": "목록 커서가 올바르지 않습니다.",
    "details": {
      "cursor": "bad-cursor"
    },
    "traceId": "req_..."
  }
}
```

## Auction Bids

`POST /api/v1/auctions/{auction_id}/bids` requires `Authorization: Bearer <accessToken>`.

Request:

```json
{
  "amount": 750000
}
```

Rules:

- `amount` must be at least `1,000` KRW greater than the auction's current price.
- Auction `status` must be `active`.
- If `endsAt` is set, it must be later than the server's current time.
- A successful bid writes an `auction_bids` row and updates `auctions.current_price` and `auctions.bid_count` in the same transaction.
- A successful bid also writes an `auction.bid.placed` transactional outbox event for search freshness, activity ranking, and outbid notifications.
- The bid event payload includes `previousHighestBidderUserId`. It is `null` for the first accepted bid and equals the previous top bidder when another user is outbid.

Response:

```json
{
  "id": "bid-id",
  "auctionId": "auction-id",
  "userId": "user-id",
  "amount": 750000,
  "createdAt": "2026-05-29T09:00:00Z"
}
```

Not included in this slice: payment capture, auto-winning, bid cancellation, proxy bidding, anti-sniping extension, and public bidder display policy.

## Error Codes

Implemented Product API errors:

| Code | HTTP | Meaning |
| --- | ---: | --- |
| `PRODUCT_NOT_FOUND` | 404 | Product id does not exist. |
| `DEAL_NOT_FOUND` | 404 | Deal id does not exist. |
| `AUCTION_NOT_FOUND` | 404 | Auction id does not exist. |
| `AUCTION_ALREADY_ENDED` | 409 | Auction is inactive or its `endsAt` is in the past. |
| `BID_TOO_LOW` | 409 | Bid amount is below the fixed 1,000 KRW minimum increment. |
| `UNAUTHORIZED` | 401 | Bid request is missing a valid bearer token. |
| `INVALID_SEARCH_CURSOR` | 400 | Cursor id is invalid for the requested list. |
| `VALIDATION_ERROR` | 422 | Pydantic/FastAPI request validation failed. |

Frontend code should branch on `code`, not Korean `message`.

## Local Runtime Check

Run PostgreSQL and apply migrations:

```bash
docker compose --profile core up -d postgres
uv run alembic -c apps/api/alembic.ini upgrade head
```

If local port `5432` is already in use, run PostgreSQL on another host port and pass the matching `DATABASE_URL`:

```bash
POSTGRES_PORT=55432 docker compose --profile core up -d postgres
DATABASE_URL=postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:55432/dealmoa \
  uv run alembic -c apps/api/alembic.ini upgrade head
```

Run the API locally:

```bash
DATABASE_URL=postgresql+psycopg://dealmoa:dealmoa-local-password@localhost:5432/dealmoa \
  uv run --directory apps/api uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then call `GET http://localhost:8000/api/v1/products`.
