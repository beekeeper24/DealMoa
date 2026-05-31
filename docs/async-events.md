# Async Events Foundation

This slice adds the first real Kafka/Celery code boundary while keeping product APIs coherent and locally testable.

## Scope

- API writes domain events to a transactional outbox table.
- `apps/consumer` polls unpublished outbox events and publishes them to Kafka.
- `apps/worker` exposes initial Celery task entry points.
- Docker Compose has separate `event` and `worker` profiles.

The initial foundation added the outbox, publisher, and worker boundary. Follow-up slices now use the same Kafka stream for Elasticsearch indexing, product-favorite notification generation, outbid notifications, and auction favorite search freshness.

## Transactional Outbox

The `domain_events` table stores API-side domain events in the same DB transaction as the domain mutation.

Initial event types:

| Event | Aggregate | Producer |
| --- | --- | --- |
| `product.updated` | `product` | Product API product create/update paths |
| `deal.created` | `deal` | Product API deal create path |
| `deal.status.changed` | `deal` | Admin API deal status review path |
| `auction.created` | `auction` | Product API auction create path |
| `auction.status.changed` | `auction` | Admin API auction status review path |
| `auction.bid.placed` | `auction` | Product API auction bid path |
| `auction.favorite.created` | `auction` | Favorites API auction favorite create path |
| `auction.favorite.deleted` | `auction` | Favorites API auction favorite delete path |
| `auction.view.recorded` | `auction` | Product API auction detail view path |
| `review.verified` | `verified_review` | Admin verified review approval path |

The outbox publisher sends messages with this envelope:

```json
{
  "eventId": "event-id",
  "eventType": "deal.created",
  "aggregateType": "deal",
  "aggregateId": "deal-id",
  "payload": {},
  "occurredAt": "2026-05-28T15:00:00+00:00"
}
```

`eventId` is the idempotency key for downstream consumers.

## Kafka Consumer Runtime

`apps/consumer` has three explicit commands:

- `publish-outbox`: polls unpublished PostgreSQL outbox rows and publishes them to Kafka.
- `consume-search-index`: consumes Kafka domain events and updates the matching Elasticsearch document.
- `consume-notifications`: consumes Kafka domain events and creates product-favorite notifications.

Environment:

```text
DATABASE_URL=postgresql+psycopg://...
ELASTICSEARCH_URL=http://elasticsearch:9200
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_DOMAIN_EVENTS_TOPIC=dealmoa.domain-events
KAFKA_SEARCH_INDEX_GROUP_ID=dealmoa-search-indexer
KAFKA_NOTIFICATION_GROUP_ID=dealmoa-notification-generator
CONSUMER_POLL_INTERVAL_SECONDS=1
CONSUMER_BATCH_SIZE=100
```

Local runtime:

```bash
docker compose --profile core --profile event up --build
```

The compose `consumer` service runs `publish-outbox` by default. To run the search indexing subscriber locally:

```bash
docker compose --profile core --profile event run --rm consumer \
  uv run python -m consumer_app.main consume-search-index
```

The search indexer currently handles:

- `product.updated` -> upsert one `products_current` document.
- `deal.created` -> upsert one `deals_current` document.
- `deal.status.changed` -> upsert one `deals_current` document from the latest persisted deal state, including current `status` and `trustScore`.
- `auction.created` -> upsert one `auctions_current` document.
- `auction.status.changed` -> upsert one `auctions_current` document from the latest persisted auction state, including current `status` and `trustScore`.
- `auction.bid.placed` -> upsert one `auctions_current` document from the latest persisted auction state.
- `auction.favorite.created` / `auction.favorite.deleted` -> upsert one `auctions_current` document from the latest persisted auction state, including current `favoriteCount`.
- `auction.view.recorded` -> upsert one `auctions_current` document from the latest persisted auction state, including current 24-hour `viewMomentum`.

To run the notification subscriber locally:

```bash
docker compose --profile core --profile event run --rm consumer \
  uv run python -m consumer_app.main consume-notifications
```

The notification generator currently handles:

- `deal.created` -> create `new_deal` notifications for users who favorited the product.
- `auction.created` -> create `new_auction` notifications for users who favorited the product.
- `auction.bid.placed` -> create `auction_outbid` notification for `previousHighestBidderUserId` when another user places the winning bid.

For `auction.bid.placed`, first bids, self-outbids, missing auctions, and payloads whose previous bidder has no persisted bid on the auction are handled as no-notification cases.

Duplicate delivery is deduplicated by the notification unique target index:

```text
(user_id, type, target_type, target_id)
```

## Celery Worker Runtime

`apps/worker` currently registers these tasks:

- `dealmoa.crawl_hot_deals_mock`
- `dealmoa.ai_review_submission_mock`
- `dealmoa.rebuild_search_index`
- `dealmoa.generate_auction_ending_soon_notifications`

Environment:

```text
DATABASE_URL=postgresql+psycopg://...
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
AUCTION_ENDING_SOON_LOOKAHEAD_MINUTES=60
AUCTION_ENDING_SOON_BATCH_SIZE=100
AUCTION_ENDING_SOON_SCHEDULE_SECONDS=300
CRAWLER_SYSTEM_USER_ID=system-crawler
CRAWLER_SYSTEM_USER_EMAIL=crawler@dealmoa.local
CRAWLER_SYSTEM_USER_NICKNAME=DealMoa Crawler
```

Local runtime:

```bash
docker compose --profile core --profile worker up --build
```

`worker` runs Celery workers. `worker-beat` runs Celery beat and enqueues the auction-ending notification task every `AUCTION_ENDING_SOON_SCHEDULE_SECONDS` seconds.

`dealmoa.crawl_hot_deals_mock` is a deterministic ingestion boundary. It creates or
reuses a non-admin crawler system user and writes mock crawled deal/auction items into
`submissions` through the same submission intake use case used by the API. Items remain
`pending_review`; the task does not create Product, Deal, Auction, search documents, or
notifications. Duplicate `sourceUrl` rows are counted as duplicates instead of creating
extra queue rows.

`dealmoa.ai_review_submission_mock` is still a mock boundary. It returns
`needs_admin_review` plus a deterministic reason and does not publish content. The API
currently records the same mock review synchronously during submission intake so the
admin queue has an immediate review result; a later slice can move that call fully behind
Celery without changing the admin approval contract.

The auction-ending task scans active auctions whose `ends_at` is inside the lookahead window and creates `auction_ending_soon` notifications for users who favorited each auction. Duplicate runs are deduplicated by the notification unique target index:

```text
(user_id, type, target_type, target_id)
```

## Auction View Momentum

The auction detail API records an immutable `auction_views` row and writes `auction.view.recorded` to the transactional outbox. The search consumer handles that event by reloading the auction aggregate and upserting the `auctions_current` document with the current 24-hour `viewMomentum` count.

## Admin Status Review Events

The admin offer status APIs write `deal.status.changed` and `auction.status.changed`
events in the same transaction as the status mutation and `admin_audit_logs` row.
Search consumers reload the canonical offer row from PostgreSQL instead of trusting the
event payload. This keeps report counts out of automatic ranking while allowing admin
status decisions to affect search visibility and trust freshness.

## Submission Approval Events

Submission approval does not emit a separate `submission.approved` event yet. Approval
creates the canonical Product plus Deal/Auction rows and emits the existing
`product.updated` plus `deal.created` or `auction.created` events. Rejection writes only
the submission state and admin audit log.

## Verified Review Events

Verified review approval writes `review.verified` in the same transaction as the review
status update and `admin_audit_logs` row. The current event payload carries only the
review id, product id, user id, and rating. Downstream AI purchase-check, scoring, or
notification consumers should reload canonical review state from PostgreSQL instead of
trusting event payload text.

## Next Steps

- Add idempotent consumer tables when consumers begin producing side effects.
