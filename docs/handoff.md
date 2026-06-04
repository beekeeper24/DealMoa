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

Current integration branch is `develop`. Create each PR-sized coherent feature/MVP
slice from `develop` on a `feature/...` branch, keep checkpoint commits on that
branch, and open a PR only when the slice is integration-ready or when the user
explicitly asks for one. PRs target `develop`; merge them into `develop` only
after local verification and required CI/review checks pass.

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
- AI search: search-bar-side AI button, structured intent, filters, BM25, later vector candidates, explanation.
- Kafka: domain event stream.
- Celery + Redis: long-running/scheduled Python jobs.
- Current Kafka domain events: `deal.created`, `deal.status.changed`, `auction.created`, `auction.status.changed`, `product.updated`, `auction.bid.placed`, `auction.favorite.created`, `auction.favorite.deleted`, `auction.view.recorded`, `review.verified`.
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
- `docs/submissions.md`: user submission intake, mock AI review, admin approval, and publishing boundary.
- `docs/price-reviews.md`: price history snapshots, verified review submission, public display, and admin approval boundary.
- `docs/discussions.md`: product discussion comments, public visibility, and admin moderation boundary.
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

1. Define the next GitHub Task as a PR-sized coherent slice, not as a tiny
   intermediate implementation step.
2. Start the next coherent feature branch from `develop`.
3. Keep small substeps inside the Task acceptance criteria/checklist.
4. Open PRs only when each feature/MVP slice is integration-ready or when the
   user explicitly asks.

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
- The search header exposes admin review entry links only for hydrated admin sessions.
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

## Completed Product Deal Auction Detail Web Scope

- Product, deal, and auction search result titles link to detail pages.
- Added `/products/{productId}`, `/deals/{dealId}`, and `/auctions/{auctionId}` web routes.
- Product detail shows core metadata, specs, current deals, current auctions, price history, approved verified reviews, and product favorite control.
- Deal detail shows offer price, seller/status, linked product, external source link, deal favorite control, and authenticated report submission.
- Auction detail shows current price, bid count, seller/status, linked product, external source link, auction favorite control, authenticated report submission, and authenticated bid submission.
- Auction detail uses the fixed 1,000 KRW bid increment and updates local current price/bid count after a successful bid response.
- Realtime auction updates remain deferred.

## Completed Submission Review MVP Scope

- Added `submissions` with user candidate data, mock AI review result, status, reviewer,
  resolution, and published Product/Offer references.
- Added authenticated `POST /api/v1/submissions` and `GET /api/v1/me/submissions`.
- Duplicate `sourceUrl` submissions return the existing submission.
- Added admin-only `GET /api/v1/admin/submissions` and
  `PATCH /api/v1/admin/submissions/{submission_id}`.
- Approval creates Product plus Deal/Auction by default, or attaches the new offer to an
  existing Product when admin approval includes `targetProductId`.
- Approval emits the existing `product.updated` plus `deal.created` or
  `auction.created` events.
- Rejection records the admin decision without publishing content.
- Approval and rejection write `admin_audit_logs`.
- `apps/worker` mock AI review task returns the same deterministic review result used
  by submission intake.
- Added `/submit` user web form and `/admin/submissions` admin review queue.
- The search header links to user submission, and admin sessions can enter both report
  and submission review queues.
- Real AI provider, server-side rate limit store, URL reputation checks, product merge UI,
  crawler ingestion, and a dedicated user submissions page remain deferred.

## Completed Price History And Verified Review Foundation Scope

- Added immutable product price-history snapshots.
- Deal creation records sale-price snapshots.
- Auction creation and accepted auction bids record current-price snapshots.
- Added public `GET /api/v1/products/{product_id}/price-history`.
- Added authenticated `POST /api/v1/products/{product_id}/verified-reviews`.
- Verified review intake records mock AI first-pass results and stays `pending_review`.
- Added admin-only verified review queue and approve/reject API.
- Admin review writes `admin_audit_logs`; approval writes a `review.verified` outbox event.
- Product detail now shows price history and approved verified reviews.
- Public verified-review responses exclude internal user ids, proof references, AI review
  text, admin reviewer ids, and resolution notes.
- Receipt upload/OCR, real AI provider integration, review scoring impact, and My Page
  review history remain deferred.

## Completed AI Assistant Foundation Scope

- Added `POST /api/v1/ai/search`.
- Added deterministic `SearchIntent` parsing for allowlisted target types and filters.
- AI search calls existing product/deal/auction search use cases and returns grouped
  candidates with a stable summary.
- Added `GET /api/v1/ai/products/{product_id}/purchase-check`.
- Purchase checks use product metadata, active deals/auctions, price history, and approved
  verified reviews.
- Purchase-check responses return deterministic `buy` / `watch` / `avoid` recommendations
  plus public-safe evidence.
- Search UI AI button opens an AI result panel.
- Product detail exposes an AI purchase-check button and report panel.
- AI search and purchase-check provider conversion, vector embeddings, prompt
  persistence, streaming, personalization, and community sentiment summarization remain
  deferred.

## Completed Product Discussion Foundation Scope

- Added `product_discussion_comments` with product, user, body, moderation status,
  moderator, note, and timestamps.
- Added public `GET /api/v1/products/{product_id}/discussions` for visible comments.
- Added authenticated `POST /api/v1/products/{product_id}/discussions`.
- Added admin-only `GET /api/v1/admin/discussions` and
  `PATCH /api/v1/admin/discussions/{comment_id}` for hide/restore moderation.
- Admin discussion moderation writes `admin_audit_logs`.
- Product detail now shows visible discussion comments and an authenticated comment form.
- Added `/admin/discussions` web queue with visible/hidden filters, pagination,
  hide/restore actions, and moderation note input.
- Added deterministic comment moderation risk signals for external contact attempts,
  repeated URLs, and obvious commercial-spam phrases.
- Admin discussion queues expose `riskScore`, `riskLevel`, and `riskReasons` and order
  comments by risk priority within each visibility status.
- Public discussion responses exclude internal user ids, moderation notes, and reviewer ids.
- Public discussion responses also exclude moderation risk fields.
- Discussion text is rendered as plain React text and is not used as AI purchase-check
  evidence or ranking signal.
- Risk signals do not automatically hide, delete, rank, or penalize comments/users.
- Nested replies, voting, notifications, author edit/delete, spam/rate-limit hardening,
  and AI summarization remain deferred.

## Completed Product Matching Foundation Scope

- Added deterministic Product match suggestions for pending submissions using normalized
  model, brand, category, and product-name token overlap.
- Added admin-only `GET /api/v1/admin/submissions/{submission_id}/product-matches`.
- Extended admin submission approval with optional `targetProductId`.
- Approval without `targetProductId` keeps the old behavior and creates a new Product.
- Approval with `targetProductId` attaches the new deal/auction to the existing Product,
  records published IDs on the submission, and emits the existing product/offer outbox
  events.
- Admin submission web queue now shows match candidates and lets admins choose existing
  Product or new Product publishing.
- Matching suggestions are admin hints only; they never auto-publish content.
- Real crawler ingestion, vector/AI matching, product merge UI, and background duplicate
  cleanup remain deferred.

## Completed Crawler Ingestion Foundation Scope

- `dealmoa.crawl_hot_deals_mock` now writes deterministic mock crawled items into
  `submissions` instead of returning only a placeholder summary.
- The worker creates or reuses a non-admin crawler system user configured by
  `CRAWLER_SYSTEM_USER_ID`, `CRAWLER_SYSTEM_USER_EMAIL`, and
  `CRAWLER_SYSTEM_USER_NICKNAME`.
- Crawler-created submissions reuse the existing submission intake use case and mock AI
  first-pass review.
- Repeated crawls are idempotent by existing `sourceUrl` uniqueness and return duplicate
  counts in the task summary.
- Crawler ingestion creates only `pending_review` submissions; admin approval remains the
  only Product/Deal/Auction publishing path.
- Live HTTP crawling, source allowlists, parser plugins, crawl scheduling changes, and
  real source reputation checks remain deferred.

## Completed Crawler Source Reputation Scope

- Added worker-side crawler source profiles configured by `CRAWLER_SOURCE_PROFILES`.
- Source profile format is `host:reputation:action`; supported reputations are
  `trusted`, `standard`, and `low`, and supported actions are `allow` and `block`.
- Added a crawler parser boundary that maps allowlisted raw items into
  `SubmissionCreateRequest` payloads.
- Unknown and blocked source hosts are skipped before database writes.
- Crawler task summary now includes `accepted` and `skipped` counts in addition to
  scanned, created, and duplicates.
- Accepted crawler items still create only `pending_review` submissions through the
  existing intake use case.
- This slice still does not perform live HTTP fetching. Persistent source reputation
  storage remains deferred.

## Completed Live Crawler Fetch Hardening Scope

- Added `dealmoa.crawl_live_urls` as the first live HTTP crawler task.
- The task is disabled by default because `CRAWLER_LIVE_URLS` defaults to an empty value.
- Live URLs must pass `CRAWLER_SOURCE_PROFILES` before network access.
- The worker HTTP client rejects non-HTTP schemes, URL userinfo, private/reserved DNS
  results, robots.txt disallowed paths, non-HTML responses, and responses larger than
  `CRAWLER_HTTP_MAX_BYTES`.
- Runtime HTTP connections use the validated resolved IP with the original host retained
  for Host/SNI.
- Robots.txt fetch failures are conservative skips, and redirects are not followed.
- Fetched HTML is parsed through a minimal `data-dealmoa-*` article parser boundary.
- Accepted live crawler items still create only `pending_review` submissions through the
  existing intake use case.
- Source-specific parser plugins, persistent source reputation storage, production crawl
  scheduling, crawler logs/admin UI, and per-host crawl rate limiting remain deferred.

## Completed Crawler Source Parser Boundary Scope

- Added `CRAWLER_SOURCE_PARSERS` as a host-to-parser mapping configured by environment.
- Parser mapping format is `host:parser_id`.
- The current supported parser ID is `dealmoa_article`.
- Live crawler fetch still requires `CRAWLER_SOURCE_PROFILES` before network access.
- After safe fetch, the worker chooses the parser from `CRAWLER_SOURCE_PARSERS`.
- Missing parser mappings are skipped with `parser_not_configured`.
- Unsupported parser IDs are skipped with `unsupported_source_parser`.
- Parser skips happen before `SubmissionCreateRequest` validation or database writes.
- Real source-specific parser implementations, persistent parser/source metadata, and
  distributed rate windows remain deferred.

## Completed Crawler Host Rate Limit Scope

- Added `CRAWLER_MAX_URLS_PER_HOST` as a per-task-run cap for live crawler URLs.
- Default cap is `20` URLs per host per `crawl_live_urls` run.
- Source-denied URLs are still skipped by source policy before the host cap is checked.
- Same-host URLs over the cap are skipped with `host_rate_limited`.
- Over-limit URLs are skipped before HTTP fetch, parser selection, submission validation,
  or database writes.
- Different hosts have independent counters inside the task run.
- Redis-backed distributed rate windows, crawl delay policies, and production scheduling
  remain deferred.

## Completed Crawler Run Logs Scope

- Added `crawler_run_logs` for completed crawler task summaries.
- `crawl_hot_deals_mock` and `crawl_live_urls` write one successful run log per completed
  run.
- Empty `crawl_live_urls` runs are logged so admins can see that the task ran with no
  configured URLs.
- Run logs include task name, `succeeded` status, scanned/fetched/accepted/created,
  duplicate/skipped counts, skip reasons, and timestamps.
- Added admin-only `GET /api/v1/admin/crawler-runs` with cursor pagination.
- Added `/admin/crawler-runs` web page and links from existing admin review pages.
- Run logs do not store fetched HTML and do not expose crawler control buttons.
- Retry metadata, Redis-backed distributed rate windows, crawl delay policies, production
  scheduling, and manual crawler controls remain deferred.

## Completed Crawler Failed Run Logs Scope

- Added nullable `error_type` and `error_message` fields to `crawler_run_logs`.
- Successful run logs keep those fields empty.
- Failed `crawl_hot_deals_mock` and `crawl_live_urls` runs rollback the main transaction,
  then write a `failed` run log in a separate short transaction.
- Failed run logs include task name, status, count fields collected before failure,
  skip reasons, exception type, bounded redacted error message, and timestamps.
- The worker re-raises the original exception after attempting to write the failed run
  log, so Celery still sees the task as failed.
- Admin crawler run API and `/admin/crawler-runs` display the failure fields.
- Failed run logs still do not store fetched HTML.
- Retry metadata, Redis-backed distributed rate windows, crawl delay policies,
  production scheduling, and manual crawler controls remain deferred.

## Completed Admin Crawler Manual Trigger Scope

- Added admin-only `POST /api/v1/admin/crawler-runs/trigger`.
- The trigger accepts only `crawl_hot_deals_mock` and `crawl_live_urls`.
- The API dispatches `dealmoa.<task>` through Celery using `CELERY_BROKER_URL`.
- The API does not import worker task code, accept arbitrary task names, or accept
  per-request crawler URLs.
- Added `CELERY_BROKER_URL` to API settings and docker-compose API environment.
- Added `/admin/crawler-runs` buttons for Mock and Live crawler execution.
- The web page shows the returned Celery task id and refreshes the first page of run
  logs after a successful trigger request.
- Live crawler source profiles, parser mappings, SSRF-safe fetch checks, robots policy,
  response-size limits, and per-host run caps remain enforced by the worker.
- Scheduler controls, retry metadata, per-request URL input, and distributed rate windows
  remain deferred.

## Completed My Page Contribution History Scope

- Added `/me` as an authenticated My Page contribution history.
- The page reads only `GET /api/v1/me/submissions`; it does not call admin submission
  APIs.
- Users can see their own submission status, source link, AI first-pass reason,
  resolution note, and published Product/Deal/Auction links when available.
- The page supports cursor pagination through the existing `nextCursor` contract.
- Search header links authenticated sessions to `/me`, and successful submission flow
  links to the new history page.
- Backend API tests now assert that `/me/submissions` does not expose another user's
  submissions.
- Favorites, notifications history, verified review history, connected accounts,
  edit/resubmit, and richer account settings remain deferred.

## Completed AI Review Provider Boundary Scope

- Added a shared AI first-pass review provider port for submissions and verified reviews.
- The default provider remains deterministic mock, preserving local and CI behavior.
- Added an OpenAI provider adapter that calls the Responses API with strict JSON schema
  output and validates the result with Pydantic.
- Allowed AI review decisions are `needs_admin_review` and `reject_candidate`; both are
  evidence only and never publish content.
- Provider failures, invalid JSON, or invalid schema output fall back to
  `needs_admin_review`.
- Verified-review `proofReference` is not sent to the model in this slice.
- Added `AI_REVIEW_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
  `OPENAI_REVIEW_MODEL`, and `OPENAI_TIMEOUT_SECONDS` settings.
- Receipt image upload, OCR engine integration, async background review migration,
  provider cost controls, rate limits, abuse logging, and monitoring remain deferred.

## Cautions

- Do not commit `.env` or real OAuth/JWT secrets.
- Do not implement direct checkout/payment flows.
- Do not make AI a floating chatbot; use search-side entry points.
- Do not let report counts directly hide or down-rank content.
- Do not use FastAPI `HTTPException` inside domain/use case code for business errors.
- Do not introduce Turborepo/Nx in the first scaffold.
