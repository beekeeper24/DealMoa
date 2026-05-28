# DealMoa Handoff

## Current Status

The project is in planning/setup. The active working path is:

```text
\\wsl.localhost\Ubuntu\home\beekeeper24\projects\DealMoa
```

Repository:

```text
https://github.com/beekeeper24/DealMoa.git
```

Current integration branch is `develop`. Active Async Events Foundation work continues on:

```text
feature/async-events-foundation
```

Do not open a PR for each checkpoint commit. Keep verified checkpoint commits on this feature branch until the Async Events Foundation slice is coherent enough to integrate into `develop`, or until the user explicitly asks for a PR.

## Fixed Decisions

- Project name: `딜모아` / `DealMoa`.
- Main portfolio axis: search/recommendation backend, not ordinary shopping CRUD.
- Monorepo apps: `apps/web`, `apps/api`, `apps/worker`, `apps/consumer`.
- Frontend package manager: `pnpm`.
- Python package/environment manager: `uv`.
- Python target: `3.12` unless a core dependency forces downgrade.
- Deployment target: Vercel for `apps/web`, Railway for API/backend services.
- Environment strategy: root `.env`, committed `.env.example`, no committed secrets.
- Architecture style: practical feature-module Clean/Hexagonal style.
- Domain model: Product-centered. Deals, auctions, reviews, discussions, price history, and favorites attach to products.
- API style: REST, `/api/v1`, resource URLs, cursor pagination by default.
- Error handling: `DealMoaException -> DomainException -> ConcreteException`; global FastAPI handlers convert exceptions to consistent error responses.
- Search: PostgreSQL source of truth, Elasticsearch read models.
- Elasticsearch indexes: `products_v1`, `deals_v1`, `auctions_v1`; unified/AI search uses multi-search.
- Korean search: Nori analyzer from the first Elasticsearch setup.
- General search: text relevance first, no vector by default.
- AI search: search-bar-side AI button, structured intent, filters, BM25, vector candidates, explanation.
- Kafka: domain event stream.
- Celery + Redis: long-running/scheduled Python jobs.
- Initial Kafka events: `deal.created`, `auction.created`, `product.updated`.
- Initial Celery tasks: `crawl_hot_deals_mock`, `ai_review_submission_mock`, `rebuild_search_index`.
- Hot-deal ranking: price first, then interest/freshness/trust.
- Auction ranking: actual auction activity first.
- Reports: admin review only; no automatic down-ranking/hiding.
- User submissions and verified reviews: AI first-pass review plus admin approval.
- CI starts from Milestone 1. Playwright joins CI when frontend is introduced.

## Documentation Map

- `docs/planning.md`: product plan, features, stack, milestones.
- `docs/architecture.md`: monorepo, domain, API, Elasticsearch, Kafka/Celery, runtime architecture.
- `docs/api-error-handling.md`: error response, exception hierarchy, error-code policy.
- `docs/product-api.md`: Product/Deal/Auction REST baseline, cursor pagination, Product API error codes.
- `docs/auth.md`: OAuth/JWT/refresh token Auth MVP contract.
- `docs/favorites.md`: Product/Deal/Auction favorite API contract.
- `docs/notifications.md`: authenticated notification inbox API contract.
- `docs/async-events.md`: transactional outbox, Kafka publisher, and Celery worker boundary.
- `docs/deployment.md`: Vercel/Railway deployment contract and environment variables.
- `docs/search-ranking.md`: ranking and search decisions.
- `docs/ai-assistant.md`: AI search and purchase assistant decisions.
- `docs/performance.md`: JMeter and Playwright verification direction.
- `docs/observability.md`: Prometheus/Grafana direction.
- `docs/security-abuse.md`: abuse/security guardrails.

## Next Activation Steps

1. Continue on `feature/async-events-foundation`.
2. Keep checkpoint commits on the feature branch and push for backup/shared visibility.
3. Verify outbox, Kafka publisher, Celery task, Docker Compose profile, Docker image, and focused Kafka/Celery security checks before declaring the slice ready.
4. Open a PR into `develop` only when Async Events Foundation is integration-ready or when the user explicitly asks.

## Completed Foundation Scope

- Monorepo folder structure.
- `uv` / `pnpm` workspace setup.
- Root `.env.example`.
- Docker Compose `core` profile.
- FastAPI app with health endpoint.
- Next.js app shell.
- PostgreSQL, Redis, Elasticsearch + Nori in local infra.
- GitHub Actions CI with backend/frontend lightweight checks.

## Completed Product API MVP Scope

- Product, Deal, Auction SQLAlchemy models and Alembic migration.
- Product create/list/get API.
- Product-scoped Deal/Auction create/list API.
- Deal/Auction single-resource get API.
- Cursor pagination with `limit`, `cursor`, and `nextCursor`.
- Common error response shape for Product API not-found and invalid cursor errors.

## Completed Search Index MVP Scope

- Versioned Elasticsearch index specs for `products_v1`, `deals_v1`, and `auctions_v1`.
- Current aliases: `products_current`, `deals_current`, and `auctions_current`.
- Nori analyzer and autocomplete fields for Korean/product text search.
- Product/Deal/Auction document builders from PostgreSQL models.
- Search APIs for products, deals, and auctions under `/api/v1/search`.
- MVP reindex endpoint under `/api/v1/admin/search/reindex`.

## Completed Search UI MVP Scope

- Typed web search client for Product, Deal, and Auction search endpoints.
- Search workspace with query input, product/deal/auction tabs, loading, empty, error, result, and load-more states.
- Vitest + Testing Library coverage for API client and UI behavior.
- Playwright browser smoke test for the product search path with mocked API response.

## Completed Auth MVP Scope

- User, OAuthAccount, and RefreshToken SQLAlchemy models and Alembic migration.
- OAuth authorization URL and callback API for Google/Kakao/Naver provider boundaries.
- DealMoa JWT access token issuance and verification.
- Opaque refresh token HttpOnly cookie transport, hashing, storage, rotation, and logout revocation.
- `GET /api/v1/auth/me` bearer-token current-user lookup.
- Web login buttons, provider callback routes, OAuth state validation, and MVP access-token session storage.

## Completed Favorites MVP Scope

- Product, Deal, and Auction favorite SQLAlchemy models and Alembic migration.
- Authenticated `/api/v1/me/favorites/...` create/delete/list APIs.
- User-scoped uniqueness and cursor pagination.
- Web search-result favorite buttons using the current access-token session.

## Completed Deployment Baseline Scope

- Vercel `apps/web` and Railway API/backend service deployment contract.
- Production-facing env variable naming and `.env.example` guidance.
- Railway-compatible API container port handling through `PORT`.
- Docker Compose role clarified as local infrastructure/demo tooling.

## Completed Notifications MVP Scope

- `notifications` SQLAlchemy model and Alembic migration.
- Authenticated `/api/v1/notifications` list and unread count APIs.
- Read-one and read-all APIs scoped to the current user.
- Notification types for new deal, new auction, and auction ending-soon alerts.

## Completed Notification Generation MVP Scope

- Product favorite users receive `new_deal` notifications when a deal is created.
- Product favorite users receive `new_auction` notifications when an auction is created.
- Duplicate notifications are prevented per `(user, type, targetType, targetId)`.
- Generation use case is reusable by a later Kafka consumer; actual Kafka/Celery runtime remains deferred.

## Active Async Events Foundation Scope

- API writes `product.updated`, `deal.created`, and `auction.created` rows to a transactional outbox.
- `apps/consumer` publishes unpublished outbox events to Kafka.
- `apps/worker` registers initial Celery task entry points.
- Docker Compose exposes `event` and `worker` profiles for local Kafka/Celery runtime checks.

## Cautions

- Do not commit `.env` or real OAuth/JWT secrets.
- Do not implement direct checkout/payment flows.
- Do not make AI a floating chatbot; use search-side entry points.
- Do not let report counts directly hide or down-rank content.
- Do not use FastAPI `HTTPException` inside domain/use case code for business errors.
- Do not introduce Turborepo/Nx in the first scaffold.
