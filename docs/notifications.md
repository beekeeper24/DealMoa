# Notifications MVP

Notifications MVP fixes the authenticated notification inbox API, product-favorite fan-out boundary, and first web dropdown.

## Scope

- Store user-scoped notifications in PostgreSQL.
- Generate `new_deal` notifications when a favorited product receives a new deal.
- Generate `new_auction` notifications when a favorited product receives a new auction.
- Generate `auction_ending_soon` notifications when a favorited auction is close to ending.
- Generate `auction_outbid` notifications when another user overbids a user's current top auction bid.
- List notifications with cursor pagination.
- Filter unread notifications.
- Return unread notification count.
- Mark one notification as read.
- Mark all current-user notifications as read.
- Show a web header notification dropdown for the current logged-in session.

Out of scope for this slice:

- Email or push delivery.
- Realtime websocket/SSE notification updates.

## Generation

New deal/new auction notification generation runs from the Kafka domain-event consumer. Product API deal/auction creation writes outbox events only:

- `deal.created` is handled by `apps/consumer` `consume-notifications` and creates `new_deal` notifications for users who favorited the product.
- `auction.created` is handled by `apps/consumer` `consume-notifications` and creates `new_auction` notifications for users who favorited the product.
- `auction.bid.placed` is handled by `apps/consumer` `consume-notifications` and creates `auction_outbid` notifications for the previous highest bidder when another user places the new accepted bid.

The generation boundary lives in the notifications module, and the consumer reuses the same use case after receiving `deal.created`, `auction.created`, or `auction.bid.placed` events.

Auction ending-soon notification generation runs from Celery beat/worker:

- `worker-beat` schedules `dealmoa.generate_auction_ending_soon_notifications`.
- The task scans active auctions ending within `AUCTION_ENDING_SOON_LOOKAHEAD_MINUTES`.
- It creates `auction_ending_soon` notifications for users who favorited the auction.

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
| `auction_outbid` | Another user placed a higher accepted bid on an auction the user was leading. |

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

## Web UI

`apps/web` renders a compact notification dropdown in the search workspace header when an access token is present in the MVP web session.

- The trigger fetches and displays unread notification count.
- Opening the dropdown fetches recent notifications.
- Users can switch between all recent notifications and unread-only notifications.
- The dropdown supports cursor-based load more when the inbox has additional pages.
- Each unread notification can be marked read.
- The dropdown can mark all current notifications as read.
- Escape and outside pointer interactions close the dropdown without leaving the page.
- Logged-out users do not see the notification trigger.

## Error Behavior

- Missing bearer token: `UNAUTHORIZED`.
- Reading a missing or other-user notification: `NOTIFICATION_NOT_FOUND`.
- Invalid cursor: `INVALID_SEARCH_CURSOR`.

Routers and use cases keep using DealMoa domain exceptions rather than FastAPI `HTTPException`.
