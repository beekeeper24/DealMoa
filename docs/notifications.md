# Notifications MVP

Notifications MVP fixes the authenticated notification inbox API before event fan-out and web notification UI.

## Scope

- Store user-scoped notifications in PostgreSQL.
- Generate `new_deal` notifications when a favorited product receives a new deal.
- Generate `new_auction` notifications when a favorited product receives a new auction.
- List notifications with cursor pagination.
- Filter unread notifications.
- Return unread notification count.
- Mark one notification as read.
- Mark all current-user notifications as read.

Out of scope for this slice:

- Kafka/Celery notification fan-out.
- Auction ending-soon scheduled generation.
- Web notification popup/dropdown.
- Email or push delivery.

## Generation

Notification generation currently runs synchronously in the Product API deal/auction creation path:

- `POST /api/v1/products/{product_id}/deals` creates `new_deal` notifications for users who favorited the product.
- `POST /api/v1/products/{product_id}/auctions` creates `new_auction` notifications for users who favorited the product.

The generation boundary lives in the notifications module so a later Kafka consumer can call the same use case after receiving `deal.created` or `auction.created` events. Runtime Kafka/Celery services are not part of this MVP slice.

Duplicate rows are prevented by the unique target index:

```text
(user_id, type, target_type, target_id)
```

## Notification Types

Initial stable values:

| Type | Meaning |
| --- | --- |
| `new_deal` | A favorited product has a new deal. |
| `new_auction` | A favorited product has a new auction. |
| `auction_ending_soon` | A favorited auction is close to ending. |

## Routes

Base prefix is `/api/v1`. All routes require `Authorization: Bearer <access-token>`.

```http
GET /api/v1/notifications?limit=20&cursor=&unreadOnly=false
GET /api/v1/notifications/unread-count
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/read-all
```

## Response Shape

Notification item:

```json
{
  "id": "notification-id",
  "type": "new_deal",
  "title": "새 핫딜",
  "body": "관심 상품에 새 핫딜이 있습니다.",
  "targetType": "product",
  "targetId": "product-id",
  "metadata": {},
  "readAt": null,
  "createdAt": "2026-05-28T12:00:00Z"
}
```

List response:

```json
{
  "items": [],
  "nextCursor": null
}
```

Unread count:

```json
{
  "count": 3
}
```

Read-all response:

```json
{
  "updatedCount": 2
}
```

## Error Behavior

- Missing bearer token: `UNAUTHORIZED`.
- Reading a missing or other-user notification: `NOTIFICATION_NOT_FOUND`.
- Invalid cursor: `INVALID_SEARCH_CURSOR`.

Routers and use cases keep using DealMoa domain exceptions rather than FastAPI `HTTPException`.
