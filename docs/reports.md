# Reports

Reports are review-priority signals only. They do not directly hide content, lower
ranking, or change search documents.

## User Report API

Authenticated users can report deal and auction targets:

```http
POST /api/v1/reports/deals/{deal_id}
POST /api/v1/reports/auctions/{auction_id}
```

Request:

```json
{
  "reasonCode": "fraud",
  "description": "Suspicious external listing"
}
```

The API stores an `open` `offer_reports` row. If the same user already has an open
report for the same target, the existing row is returned instead of creating a duplicate
open report.

## Admin Queue API

Admins can list and review report rows:

```http
GET /api/v1/admin/reports?status=open&limit=20&cursor=...
PATCH /api/v1/admin/reports/{report_id}
```

Review request:

```json
{
  "status": "resolved",
  "resolutionNote": "Changed deal status to rejected",
  "targetStatus": "rejected"
}
```

Allowed report statuses are:

- `open`
- `resolved`
- `dismissed`

`targetStatus` is optional. When omitted, the review only changes the report row. When
provided, the API also changes the reported deal or auction status in the same database
transaction, writes the target status audit log, and creates the existing
`deal.status.changed` or `auction.status.changed` outbox event.

Allowed target statuses are:

- `pending`
- `active`
- `verified`
- `rejected`
- `blocked`
- `closed`

Admin report review always writes an `admin_audit_logs` row with the actor, report target,
previous report status, new report status, resolution note, and timestamps. Target status
changes write a second audit log row for the underlying deal or auction.

## Ranking Boundary

Report count does not feed `trustScore`, hot-deal ranking, auction activity ranking, or
search visibility. Admin status decisions on the underlying deal or auction are the only
review outcome that changes search visibility or status-derived trust.
