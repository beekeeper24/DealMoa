# DealMoa Architecture

## Monorepo Layout

```text
DealMoa/
  apps/
    web/        # Next.js user web. Initial admin screens also live here.
    api/        # FastAPI REST API.
    worker/     # Celery worker, crawler jobs, AI review jobs, embedding jobs.
    consumer/   # Kafka consumers, Elasticsearch indexer, notification events.
  infra/
    elasticsearch/
    kafka/
    prometheus/
    grafana/
  loadtest/
    jmeter/
  docs/
  scripts/
  docker-compose.yml
```

The apps are split by runtime responsibility from the beginning. `worker` and `consumer` may start with minimal code, but their folders exist so Celery and Kafka boundaries are visible in the portfolio structure.

## Runtime Responsibilities

- `apps/web`: user-facing UI, initial admin UI, search entry, AI button, notification popup, my page.
- `apps/api`: request validation, auth, REST API, DB transactions, domain use cases, domain event creation.
- `apps/worker`: scheduled or long-running jobs such as crawler mocks, AI first-pass review, embedding generation, and search reindex jobs.
- `apps/consumer`: Kafka event consumers that update read models, create notification candidates, and synchronize Elasticsearch indexes.
- `infra`: local development and demo infrastructure configuration.

## Architecture Style

Use a practical feature-module style inspired by Clean Architecture and Hexagonal Architecture.

```text
apps/api/app/modules/products/
  domain.py       # entities/value objects/domain rules
  ports.py        # repository/service interfaces
  use_cases.py    # application use cases
  schemas.py      # Pydantic request/response models
  repository.py   # SQLAlchemy adapter
  router.py       # FastAPI routes
  exceptions.py   # product domain exceptions
```

Rules:

- Domain/use case code does not throw FastAPI `HTTPException` directly.
- Routers stay thin and call use cases.
- Repositories/adapters implement ports.
- Add abstractions only when they protect real boundaries or remove meaningful duplication.
- Keep worker/consumer side effects idempotent where possible.

## Product-Centered Domain Model

`Product` is the center of the domain. `Deal`, `Auction`, `Review`, `CommunityPost`, `PriceHistory`, and product-level favorites connect to `Product`.

```text
Product
  ├─ Deal
  ├─ Auction
  ├─ Review
  ├─ CommunityPost
  ├─ PriceHistory
  └─ Favorite
```

This makes product detail pages, price history, product favorite alerts, verified review analysis, and AI purchase checks natural. Deal/auction ingestion must match an incoming item to a product. The first implementation can use admin/manual matching; automatic matching can later evolve from text matching to Elasticsearch candidate search and AI-assisted suggestions.

Core entities:

- `User`
- `OAuthAccount`
- `Product`
- `Deal`
- `Auction`
- `AuctionBid`
- `Favorite`
- `Notification`
- `Review`
- `CommunityPost`
- `Submission`
- `AdminReview`
- `PriceHistory`

## REST API Standards

- Use REST with `/api/v1` prefix.
- Use resource-oriented URLs, not verb-style URLs.
- Use cursor pagination by default for user-facing lists, search results, rankings, notifications, deals, and auctions.
- Allow page-number pagination only for admin screens when it is simpler for table navigation.
- Keep admin APIs under `/api/v1/admin`.
- OAuth login issues DealMoa-owned access/refresh tokens.
- Use a consistent success/error response shape.

Example routes:

```http
GET /api/v1/products
GET /api/v1/products/{product_id}
GET /api/v1/products/{product_id}/deals
GET /api/v1/products/{product_id}/auctions
POST /api/v1/products/{product_id}/favorites
DELETE /api/v1/products/{product_id}/favorites
GET /api/v1/notifications
POST /api/v1/auctions/{auction_id}/bids
```

## Elasticsearch Strategy

PostgreSQL is the source of truth. Elasticsearch stores search-oriented read models.

Use separate indexes by type:

```text
products_v1
deals_v1
auctions_v1
```

Search modes:

- Default product search: `products_v1`.
- Hot deal search: `deals_v1`.
- Auction search: `auctions_v1`.
- Unified search and AI search: multi-search across product/deal/auction indexes.

Use aliases for future reindexing:

```text
products_current -> products_v1
```

When index mapping changes, build `products_v2`, reindex, then switch the alias.

Korean search strategy:

- Use Nori analyzer from the first Elasticsearch setup.
- Support exact fields, normalized fields, n-gram/search-as-you-type fields, synonym rules, and limited fuzzy fallback.
- General search remains text relevance first; vector search belongs to AI search or recommendation paths.

## Kafka And Celery Boundary

Kafka is for domain events. Celery is for long-running or scheduled jobs.

The first implementation uses a transactional outbox table. API use cases write outbox rows in the same DB transaction as Product, Deal, and Auction mutations; `apps/consumer` publishes unpublished rows to Kafka and marks them published after the broker write succeeds.

Initial Kafka events:

- `deal.created`
- `auction.created`
- `product.updated`
- `auction.bid.placed`
- `auction.view.recorded`

Initial consumers:

- Outbox publisher from PostgreSQL to Kafka.
- Elasticsearch index synchronization.
- Interest-based notification candidate creation.

Later Kafka events:

- `favorite.product.created`
- `review.verified`
- `submission.approved`

Initial Celery tasks:

- `crawl_hot_deals_mock`
- `ai_review_submission_mock`
- `rebuild_search_index`

Later Celery tasks:

- real crawler jobs
- receipt verification
- embedding generation
- price history snapshots
- notification batches

Do not let Kafka consumers and Celery tasks produce the same side effect without an idempotency key or deduplication strategy.

## Docker Compose Profiles

- `core`: web, api, PostgreSQL, Redis, Elasticsearch + Nori.
- `worker`: Celery worker and beat.
- `event`: Kafka, Kafka UI, consumers.
- `observability`: Prometheus and Grafana.
- `loadtest`: optional JMeter support or supporting services.

Development supports both full Docker and hybrid local execution:

- Full Docker: reproducible demo and onboarding path.
- Hybrid local: DB/Redis/Elasticsearch in Docker, FastAPI/Next.js run locally for faster development.

## Deployment Targets

Production deployment targets are fixed as:

- Vercel for `apps/web`.
- Railway for `apps/api` and later backend service runtimes such as worker and consumer.
- Railway managed PostgreSQL and Redis when possible.
- Railway or an external managed Elasticsearch-compatible service for search.

Vercel should use `apps/web` as the project root and receive only browser-safe variables such as `NEXT_PUBLIC_API_BASE_URL`.

Railway should build the API from the repository root using `apps/api/Dockerfile`. The API listens on `${PORT:-8000}` so Railway can inject its service port while local Docker keeps the same image runnable.

Docker Compose is not the production target. It exists to keep local infrastructure and demo flows reproducible while using the same environment-variable contract as production.

## Error Handling

Use the project-level exception hierarchy described in `docs/api-error-handling.md`.

Important architectural rule: domain/use case code raises DealMoa domain exceptions, not HTTP framework exceptions. FastAPI exception handlers convert those exceptions into API responses.
