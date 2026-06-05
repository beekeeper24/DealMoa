# MVP Closure Audit - 2026-06-05

## Decision

DealMoa's feature MVP is complete as of 2026-06-05.

This means the planned MVP product capabilities are implemented and locally verified
enough to stop adding new feature slices before first deployment. It does not mean the
project is production-ready. The next phase is release readiness: environment audit,
full local demo smoke, Vercel/Railway setup, deployed smoke, and deployed performance
observation.

## Evidence Sources

- `docs/planning.md`
- `docs/project-planning-review-2026-05-31.md`
- `docs/handoff.md`
- `docs/performance.md`
- Current `develop` branch through PR #89

## Milestone Status

| Milestone | Status | Evidence |
| --- | --- | --- |
| 1. Project foundation | Complete | Foundation scope, CI, Docker Compose core profile, deployment baseline |
| 2. Product/search basics | Complete | Product API, search index, search UI |
| 3. Auth/favorites/notifications | Complete | Auth, favorites, notifications, notification generation, notification web UI |
| 4. Admin/submission/review workflow | Complete | Admin report UI, offer status review, submissions, product matching, crawler admin controls |
| 5. Ranking/price history/verified reviews | Complete for MVP | Hot-deal ranking, auction activity ranking, price history, verified reviews, discussion |
| 6. AI search/purchase assistant | Complete for MVP foundation | AI search, purchase check, provider boundary, safe fallback behavior |
| 7. Observability/load test/hardening | Complete for local MVP readiness | API/worker/consumer metrics, local Grafana/Prometheus, JMeter baseline, JMeter local observation |

## 2026-05-31 Gap Resolution

The 2026-05-31 planning review listed seven remaining MVP gaps. Their current status:

| Old gap | Current status | Evidence |
| --- | --- | --- |
| Admin web UI for report review and offer status changes | Complete | Completed Admin Report Web UI Scope; Completed Admin Offer Status Review Scope |
| Dedicated HotDealScore endpoint | Complete | Completed Hot Deal Ranking Scope |
| Product, deal, and auction detail pages with bid/report/favorite flows | Complete | Completed Product Deal Auction Detail Web Scope; Completed Auction Bidding Baseline Scope |
| User submission plus AI review mock and admin approval | Complete | Completed Submission Review MVP Scope; Completed AI Review Provider Boundary Scope |
| Price history plus verified review foundation | Complete | Completed Price History And Verified Review Foundation Scope; Completed Verified Review Auto-Publish Moderation Scope |
| Real AI search and purchase assistant after evidence data exists | Complete for MVP | Completed AI Assistant Foundation Scope; default provider remains mock with OpenAI adapter boundary |
| Observability and load-test implementation | Complete for local MVP readiness | Completed Local Observability Profile Scope; Completed Worker/Consumer Metrics MVP Scope; Completed JMeter Local Baseline Observation Scope |

## Feature MVP Complete

The feature MVP includes:

- Search-centered product/deal/auction browsing.
- Korean Elasticsearch indexing and local reindex path.
- Product/deal/auction detail pages.
- Hot deal and auction activity ranking.
- OAuth session flow with HttpOnly refresh-cookie transport.
- Product/deal/auction favorites.
- Notification inbox and dropdown.
- Event-driven search-index and notification generation boundaries.
- Auction bidding with 1,000 KRW minimum increment.
- User offer submission, mock AI first-pass review, admin approval, and product matching.
- Report intake, admin review queue, and admin offer status changes.
- Price history and verified purchase review auto-publish with post-publication moderation.
- Product discussions with admin moderation and risk signals.
- My Page contribution history.
- Crawler mock/live ingestion boundaries, safe fetch checks, parser mapping, run logs, and admin manual trigger.
- AI search and purchase-check MVP with deterministic mock behavior and provider adapter boundaries.
- Local observability with Prometheus/Grafana and API/worker/consumer metrics.
- Local JMeter baseline, summary tool, and 2026-06-05 Korean demo observation.

## Release Readiness Before Public Deploy

These are not new MVP features. They are the next work needed before treating the app as
deployment-ready:

1. Release-readiness checklist and environment audit.
   - Verify `.env.example` against Vercel/Railway variables.
   - Confirm no secrets or local-only values are committed.
   - Confirm OAuth callback URL, CORS, and refresh-cookie settings for split Vercel/Railway domains.
   - Confirm production metrics exposure policy.

2. Full local demo smoke.
   - Run migrations, Korean seed, reindex, API, web, worker, consumer, and observability profiles.
   - Exercise real API/Web paths, not only mocked Playwright routes.
   - Confirm admin, submission, verified review, crawler run, search, detail, AI purchase-check, and notification paths are demoable.

3. Vercel/Railway deployment setup.
   - Create/import Vercel web project rooted at `apps/web`.
   - Create Railway API service from `apps/api/Dockerfile`.
   - Provision PostgreSQL, Redis, and reachable Elasticsearch.
   - Decide first deployed worker/consumer strategy.
   - Run Alembic as an explicit release operation.

4. Deployed smoke and deployed baseline.
   - Verify Vercel web to Railway API connection.
   - Verify OAuth callback behavior after production URLs are registered.
   - Run deployed API smoke checks.
   - Run a small deployed JMeter observation and record the result separately from local demo numbers.

## Post-MVP Backlog

These items are intentionally outside the first feature MVP:

- Direct checkout/payment.
- Production SLOs and CI-gated performance thresholds.
- Search-result caching.
- Vector embeddings in ordinary search.
- Streaming AI responses and prompt persistence.
- Receipt image upload, OCR, and image-storage policy.
- Real large-scale crawler source parsers and persistent source reputation storage.
- Distributed crawler rate windows and production crawl scheduling.
- Realtime auction updates, realtime notification push/SSE, and a dedicated full notification page.
- Product merge UI, background duplicate cleanup, and AI/vector product matching.
- Review scoring impact, community sentiment summarization, and consumer report buttons for verified reviews.
- Production Prometheus/Grafana dashboards, alert rules, backing-service exporters, Kafka lag exporters, and Celery multiprocess metrics.

## Next PR Order

1. Release-readiness checklist and environment audit.
2. Full local demo smoke with real API/Web runtime.
3. Vercel/Railway deployment configuration pass.
4. First deployed smoke verification.
5. Deployed JMeter observation and performance note.

## Operating Decision

Stop adding feature slices until the release-readiness sequence above is complete or a
specific blocker requires a small fix. New feature work should move to post-MVP backlog
unless it is necessary to make the first deployment coherent.
