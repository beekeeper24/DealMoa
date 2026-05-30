# Favorites MVP

Favorites MVP adds authenticated save/unsave behavior for products, deals, and auctions.

## Scope

- Users can favorite products, deals, and auctions.
- Favorite creation is idempotent per `(user, target)` pair.
- Favorite deletion is idempotent when the target exists.
- Favorite list endpoints are cursor-paginated.
- Web search results expose a simple favorite toggle when an access-token session exists.

My-page favorite aggregation and realtime alert delivery are out of scope for this slice.
Auction favorites feed `favoriteCount` as an activity ranking interest signal during
search reindex and auction document upserts. Auction favorite create/delete mutations write
`auction.favorite.created` and `auction.favorite.deleted` outbox events only for real row
changes, so duplicate favorite creates or repeated deletes do not emit extra search refresh
events.

## Routes

Base prefix is `/api/v1`.

```http
PUT /api/v1/me/favorites/products/{product_id}
DELETE /api/v1/me/favorites/products/{product_id}
GET /api/v1/me/favorites/products?limit=20&cursor=

PUT /api/v1/me/favorites/deals/{deal_id}
DELETE /api/v1/me/favorites/deals/{deal_id}
GET /api/v1/me/favorites/deals?limit=20&cursor=

PUT /api/v1/me/favorites/auctions/{auction_id}
DELETE /api/v1/me/favorites/auctions/{auction_id}
GET /api/v1/me/favorites/auctions?limit=20&cursor=
```

All routes require `Authorization: Bearer <access-token>`.

## Response Shape

Product favorite:

```json
{
  "id": "favorite-id",
  "productId": "product-id",
  "createdAt": "2026-05-28T00:00:00Z"
}
```

List response:

```json
{
  "items": [],
  "nextCursor": null
}
```

Deal and auction responses use `dealId` and `auctionId`.

## Error Behavior

- Missing bearer token: `UNAUTHORIZED`.
- Missing product/deal/auction target: existing `PRODUCT_NOT_FOUND`, `DEAL_NOT_FOUND`, or `AUCTION_NOT_FOUND`.
- Invalid list cursor: `INVALID_SEARCH_CURSOR`.

Routers and use cases keep using DealMoa domain exceptions rather than FastAPI `HTTPException`.
