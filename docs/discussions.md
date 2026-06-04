# Product Discussions

## Scope

Product discussions are lightweight product-scoped comments. They let logged-in
users discuss a product on the product detail page without making community
opinion part of AI purchase-check evidence or ranking.

This foundation slice includes flat comments only:

- Public visible-comment list.
- Authenticated comment creation.
- Admin moderation queue filtered by comment status.
- Admin hide/restore action with audit logs.
- Deterministic moderation risk signals for admin review priority.

Deferred:

- Nested replies.
- Votes, likes, or ranking impact.
- Notifications.
- Author edit/delete.
- Rich text, image upload, or markdown rendering.
- AI summarization or sentiment analysis.

## Routes

Base prefix is `/api/v1`.

```http
GET /api/v1/products/{product_id}/discussions
POST /api/v1/products/{product_id}/discussions
GET /api/v1/admin/discussions?status=visible
PATCH /api/v1/admin/discussions/{comment_id}
```

Public list responses include only visible comments and expose nickname, not
internal user/admin metadata:

```json
{
  "items": [
    {
      "id": "comment-id",
      "productId": "product-id",
      "userNickname": "Deal User",
      "body": "이 가격이면 실사용 기준으로 괜찮아 보입니다.",
      "createdAt": "2026-06-01T00:00:00Z",
      "updatedAt": "2026-06-01T00:00:00Z"
    }
  ],
  "nextCursor": null
}
```

Comment creation requires `Authorization: Bearer <accessToken>`.

```json
{
  "body": "이 가격이면 실사용 기준으로 괜찮아 보입니다."
}
```

The MVP stores new comments as `visible`. Later abuse hardening can introduce
rate limits, spam review, or pending states without changing the public list
contract.

On creation, comments are analyzed by deterministic moderation rules. The stored
signals are `riskScore`, `riskLevel`, and `riskReasons`. Current reasons include
external contact attempts, repeated URLs, and obvious commercial-spam phrases.
These signals are advisory only: they do not automatically hide, delete, rank,
or penalize the author.

## Moderation

Statuses:

- `visible`: shown on product detail.
- `hidden`: hidden by admin moderation.

Admin actions:

- `hide`
- `restore`

Request:

```json
{
  "action": "hide",
  "moderationNote": "욕설 포함"
}
```

Admin moderation requires `role = ADMIN`. Each hide/restore writes an
`admin_audit_logs` row with action `discussion_comment.hidden` or
`discussion_comment.restored`.

Admin list responses include risk fields and order comments within the selected
status by risk score first, then newest first. Public responses do not include
risk fields.

## Web Behavior

Product detail calls `GET /api/v1/products/{product_id}/discussions?limit=10`
alongside the product, offers, price history, and approved verified reviews.

The web UI renders comment bodies as React text with `white-space: pre-wrap`.
It does not use raw HTML rendering. Anonymous users can read visible comments
but must log in before posting.

Admins can review comments at `/admin/discussions`. The page supports visible
and hidden filters, cursor pagination, hide/restore actions, and optional
moderation notes. It does not let admins edit comment bodies or delete comments.

## Security Boundaries

- Discussion creation requires login.
- Public responses exclude user ids, moderation notes, reviewer ids, and hidden
  comments. They also exclude moderation risk fields.
- Comment content is not used as AI purchase-check evidence.
- Comment count and report count do not change offer ranking or trust scores.
- Admin hide/restore is the only visibility mutation in this slice.
- Risk signals do not automatically hide, delete, rank, or penalize comments/users.
- Admin discussion web actions require the same bearer-token admin session as
  the admin API.
