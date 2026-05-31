# DealMoa Handoff

## Current Status

The project is past foundation/planning and is in MVP feature build-out. The
active working path is:

```text
\\wsl.localhost\Ubuntu\home\beekeeper24\projects\DealMoa
```

Repository:

```text
https://github.com/beekeeper24/DealMoa.git
```

Current integration branch is `develop`. Create each coherent feature/MVP slice from `develop` on a `feature/...` branch, keep checkpoint commits on that branch, and open a PR only when the slice is integration-ready or when the user explicitly asks for one.

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
- Current Kafka domain events: `deal.created`, `deal.status.changed`, `auction.created`, `auction.status.changed`, `product.updated`, `auction.bid.placed`, `auction.favorite.created`, `auction.favorite.deleted`, `auction.view.recorded`.
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
- `docs/reports.md`: report intake, admin review queue, and ranking boundary.
- `docs/async-events.md`: transactional outbox, Kafka publisher, and Celery worker boundary.
- `docs/deployment.md`: Vercel/Railway deployment contract and environment variables.
- `docs/search-ranking.md`: ranking and search decisions.
- `docs/ai-assistant.md`: AI search and purchase assistant decisions.
- `docs/performance.md`: JMeter and Playwright verification direction.
- `docs/observability.md`: Prometheus/Grafana direction.
- `docs/security-abuse.md`: abuse/security guardrails.
- `docs/project-planning-review-2026-05-31.md`: one-time whole-project planning
  validation, current MVP gaps, next PR sequence, and workflow usage rules.

## Next Activation Steps

1. Start the next coherent feature branch from `develop`.
2. Next PR sequence: admin report/status Web UI, dedicated hot-deal ranking
   endpoint, product/deal/auction detail MVP, user submission plus AI review mock
   and admin approval, then price history plus verified review foundation.
3. Open PRs only when each feature/MVP slice is integration-ready or when the user explicitly asks.

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
- Web login buttons, provider callback routes, OAuth state validation, and refresh-cookie session recovery.

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

## Completed Async Events Foundation Scope

- API writes `product.updated`, `deal.created`, and `auction.created` rows to a transactional outbox.
- `apps/consumer` publishes unpublished outbox events to Kafka.
- `apps/worker` registers initial Celery task entry points.
- Docker Compose exposes `event` and `worker` profiles for local Kafka/Celery runtime checks.

## Completed Event Search Indexing Scope

- Search client supports single-document upsert through the current aliases.
- `apps/consumer` handles `product.updated`, `deal.created`, and `auction.created` events for Elasticsearch indexing.
- `apps/consumer` handles `deal.status.changed` and `auction.status.changed` by rebuilding the current offer search document with fresh status/trust fields.
- `apps/consumer` handles `auction.bid.placed` by rebuilding the `auctions_current` document from persisted auction state.
- `apps/consumer` handles `auction.view.recorded` by rebuilding the auction document with current view momentum.
- Kafka subscriber command `consume-search-index` is separate from the outbox publisher command.
- Admin full reindex remains the recovery path.

## Completed Auction Activity Ranking Scope

- Auction search documents include `uniqueBidderCount` from accepted bid rows.
- Auction search documents include `favoriteCount` from auction favorite rows.
- Auction search documents include `viewMomentum` from auction detail views in the last 24 hours.
- Auction and deal search documents include status-derived `trustScore`.
- Full auction reindex eagerly loads bids to compute unique bidder counts without N+1 queries.
- Full auction reindex bulk-loads favorite and view-momentum counts, and single auction upserts query current counts.
- General deal and auction search filters to `status = active`.
- `GET /api/v1/search/auctions/activity` returns active auctions ordered by Elasticsearch script score.
- The current score uses available signals: capped bid count, capped unique bidder count, view momentum, favorite-count interest, ending-soon pressure, and status-derived trust.

## Completed Hot Deal Ranking Scope

- Deal search documents include `favoriteCount` from deal favorite rows.
- Full deal reindex bulk-loads favorite counts, and single deal upserts query the
  current favorite count.
- `GET /api/v1/search/deals/hot` returns active deals ordered by Elasticsearch script score.
- The current score uses available signals: capped discount ratio from original/sale
  price, capped favorite-count interest, 72-hour freshness, and status-derived trust.
- General deal search remains text-relevance-first.
- Deal favorite create/delete event freshness remains deferred; favorite-count ranking
  freshness depends on reindex or deal document refresh until that slice is implemented.

## Completed Admin Offer Status Review Scope

- Added `admin_audit_logs` with actor, target, action, previous status, new status, reason, and timestamps.
- Added admin-only `PATCH /api/v1/admin/deals/{deal_id}/status`.
- Added admin-only `PATCH /api/v1/admin/auctions/{auction_id}/status`.
- Admin status updates require bearer auth and `role = ADMIN`; non-admin users receive `FORBIDDEN`.
- Status updates write immutable audit logs and transactional outbox events.
- `deal.status.changed` and `auction.status.changed` refresh Elasticsearch read models through the search consumer.
- Report counts still do not directly hide or down-rank content.

## Completed Report Review Queue Scope

- Added `offer_reports` with user, target, reason, status, reviewer, resolution, and timestamps.
- Added authenticated `POST /api/v1/reports/deals/{deal_id}`.
- Added authenticated `POST /api/v1/reports/auctions/{auction_id}`.
- Duplicate open reports from the same user for the same target return the existing open report.
- Added admin-only `GET /api/v1/admin/reports`.
- Added admin-only `PATCH /api/v1/admin/reports/{report_id}` for `resolved` / `dismissed` report review.
- Admin report list/review responses include a `target` summary with target type, ID,
  title, current status, seller, and source URL for initial web admin queue rendering.
- Admin report review writes `admin_audit_logs`.
- Admin report review can include optional `targetStatus` to change the reported deal or
  auction status in the same transaction.
- Report counts still do not directly change offer status, search visibility, or ranking.
  Only explicit admin status decisions do.

## Completed Admin Report Web UI Scope

- Added `/admin` web route for the admin report review queue.
- Admin users can filter reports by `open`, `resolved`, and `dismissed`.
- Report cards show target summary, current target status, seller, source URL, reason,
  description, reporter, and created time.
- Admin users can resolve or dismiss a report and optionally change the reported deal
  or auction status in the same action.
- The search header shows an `관리자` entry link only for hydrated admin sessions.
- Anonymous users and authenticated non-admin users receive explicit access guidance.

## Completed Auction Favorite Event Freshness Scope

- Auction favorite create/delete mutations write `auction.favorite.created` and `auction.favorite.deleted` outbox events.
- Idempotent duplicate favorite creates and repeated deletes do not emit extra events.
- The search consumer handles auction favorite events by reloading the auction from PostgreSQL and upserting the current `auctions_current` document.
- Auction search `favoriteCount` now stays fresh after favorite mutations without waiting for a full reindex.

## Completed Event Notification Generation Scope

- Product API no longer writes notification rows synchronously for new deal/new auction creation.
- Product API still writes `deal.created`, `auction.created`, and `auction.bid.placed` outbox events in the offer/bid mutation transaction.
- `auction.bid.placed` payload includes `previousHighestBidderUserId` so outbid notifications can be generated asynchronously.
- `apps/consumer` `consume-notifications` handles `deal.created`, `auction.created`, and `auction.bid.placed`.
- Outbid notifications are skipped for first bids, self-outbids, missing auctions, and previous-bidder payloads that do not match persisted auction bid history.
- Existing unique notification target index prevents duplicate Kafka delivery from creating duplicate notifications.

## Completed Auction Ending Notifications Scope

- `apps/worker` registers `dealmoa.generate_auction_ending_soon_notifications`.
- Celery beat schedules the task through `worker-beat`.
- The task scans active auctions ending within the configured lookahead window.
- Users who favorited those auctions receive `auction_ending_soon` notifications.
- Existing unique notification target index prevents duplicate scheduled runs from creating duplicate notifications.

## Completed Notification Web UI Scope

- `apps/web` adds a typed notifications API client.
- Search workspace header renders a notification dropdown only for logged-in sessions.
- The dropdown fetches unread count, lists recent notifications, marks one notification read, and marks all notifications read.
- The dropdown can switch between all and unread-only notifications, load additional cursor pages, and close on Escape or outside pointer interaction.
- Realtime push/SSE and a dedicated full notification page remain deferred.

## Completed Auth Hydration Polish Scope

- Auth-dependent web UI starts from a neutral session-checking state during server render and first client render.
- Browser auth sessions are recovered after mount by calling `POST /api/v1/auth/token/refresh` with the HttpOnly refresh cookie.
- Access tokens are kept in React memory only; legacy `dealmoa.authSession` storage is cleared instead of read.
- `AuthSessionProvider` is mounted at the app root so auth status, notifications, and favorite buttons share one in-memory session snapshot and one refresh-cookie hydration result.

## Completed Auction Bidding Baseline Scope

- Add `auction_bids` as the immutable record of accepted user bids.
- `POST /api/v1/auctions/{auction_id}/bids` requires bearer auth.
- Accepted bids must be at least 1,000 KRW above the current auction price.
- Successful bids update `auctions.current_price` and `auctions.bid_count` in the same transaction.
- Low bids and ended/inactive auctions use DealMoa domain exceptions and common error responses.
- Successful bids write `auction.bid.placed` outbox events; the search consumer now uses them for auction document freshness.

## Cautions

- Do not commit `.env` or real OAuth/JWT secrets.
- Do not implement direct checkout/payment flows.
- Do not make AI a floating chatbot; use search-side entry points.
- Do not let report counts directly hide or down-rank content.
- Do not use FastAPI `HTTPException` inside domain/use case code for business errors.
- Do not introduce Turborepo/Nx in the first scaffold.
