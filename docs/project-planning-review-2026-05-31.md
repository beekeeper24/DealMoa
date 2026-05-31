# Project Planning Review - 2026-05-31

## Purpose

This is the one-time whole-project planning validation agreed before continuing
implementation. The review used the existing planning docs and current repository
state to check whether the product direction, milestone order, and next MVP slices
still fit DealMoa.

Reviewed sources:

- `docs/planning.md`
- `docs/handoff.md`
- `docs/architecture.md`
- `docs/search-ranking.md`
- `docs/auth.md`
- `docs/reports.md`
- `docs/deployment.md`
- `docs/security-abuse.md`
- Current app tree under `apps/api`, `apps/web`, `apps/consumer`, and `apps/worker`

The OMX `ralplan` workflow was run in read-only mode. It reached chat-only
Planner/Architect/Critic consensus, but did not persist `.omx` artifacts because
the run was intentionally read-only.

## Consensus

Status: approve with sequencing changes.

The core product and technical direction remains consistent:

- DealMoa is a search, ranking, alerting, and purchase-decision support service,
  not a direct checkout shopping mall.
- PostgreSQL remains the source of truth.
- Elasticsearch remains the search and ranking read model.
- Basic search should stay text-relevance first. Vector search belongs to AI
  search, not ordinary product search.
- Kafka handles domain events. Celery handles scheduled or long-running jobs.
- Reports remain admin review signals only. Report counts do not directly hide,
  down-rank, or block content.
- OAuth/JWT access tokens plus HttpOnly refresh cookies remain the auth direction.

## Milestone Assessment

The original milestone order is still valid:

1. Foundation
2. Product and search basics
3. Auth, favorites, and notifications
4. Admin, submissions, and review workflow
5. Ranking, price history, and verified reviews
6. AI search and purchase assistant
7. Observability, load test, and hardening

Actual implementation has sensibly mixed parts of those milestones:

- M1 to M3 are mostly complete.
- Auction activity ranking from M5 has already advanced because ranking is a core
  portfolio axis.
- Admin report/status backend pieces from M4 exist, but admin web UI, user
  submissions, approval workflow, and verified reviews remain open.
- AI search currently has only an entry point placeholder and should wait until
  price history, verified reviews, and detail flows exist.

This sequencing is acceptable. The next priority should be turning existing
backend capability into demoable end-to-end flows before adding broader AI
features.

## Current Completed Coverage

Completed coverage includes:

- Monorepo foundation, `uv` and `pnpm` workspaces, CI, local infra profiles, and
  deployment baseline for Vercel/Railway.
- Product, deal, and auction baseline REST APIs.
- Elasticsearch index definitions, reindexing, and product/deal/auction search.
- Search UI with tabs, pagination, favorites, auth session hydration, and
  notification dropdown.
- OAuth provider boundaries, access-token issuance, refresh-cookie rotation, and
  current-user lookup.
- Product/deal/auction favorites.
- Notifications API and async notification generation through the consumer.
- Transactional outbox, Kafka consumer foundation, and Celery worker foundation.
- Auction bidding baseline.
- Auction activity ranking signals and endpoint.
- Admin deal/auction status APIs, audit logs, report intake, report review queue,
  and optional target status change.
- Auction ending-soon notification task.

## Remaining MVP Gaps

Main gaps:

1. Admin web UI for report review and offer status changes.
2. Dedicated hot-deal ranking endpoint using the documented HotDealScore.
3. Product, deal, and auction detail pages with bid/report/favorite flows.
4. User submission flow with AI first-pass mock and admin approval.
5. Price history and verified review foundation.
6. Real AI search and purchase assistant after evidence data exists.
7. Observability and load-test implementation.

## Recommended Next PR Slices

1. Admin report/status Web UI
   - Render the existing admin report queue.
   - Show target summary.
   - Resolve or dismiss reports.
   - Optionally change target status in the same admin action.

2. Dedicated HotDealScore endpoint
   - Add an active hot-deal ranking endpoint.
   - Use price, interest, freshness, and trust signals.
   - Keep reports out of direct scoring unless an admin action changes status.

3. Product/Deal/Auction detail MVP
   - Link search results to detail pages.
   - Include auction bidding, report button, favorite state, and core offer data.

4. User submission plus AI review mock and admin approval
   - Add submission intake, duplicate URL handling, rate limits, AI mock review,
     admin queue, and approval flow.

5. Price history plus verified review foundation
   - Add evidence data needed for later AI purchase checks.
   - Keep verified reviews behind approval.

AI search and purchase assistant should follow after these slices because it
needs trustworthy evidence data to avoid becoming a thin explanation layer.

## Risks And Operating Rules

Key risks:

- Backend features can outpace demoable web flows.
- AI can be added too early without evidence data.
- Kafka and Celery side effects can overlap unless idempotency rules stay clear.
- Handoff and domain docs can drift from implementation.
- Admin and user-generated-content paths require strong authorization, audit, and
  state-transition tests.

Workflow rules:

- Do not run `ralplan` for every slice.
- Use `ralplan` for milestone-order changes, broad cross-app changes, AI scope,
  auth/admin/security/eventing decisions, or unclear acceptance criteria.
- Use the main Codex flow for small documented endpoint work, clear UI wiring,
  tests, and straightforward fixes.
- Use TDD for ranking, auth, admin authorization, event idempotency, migrations,
  and state transitions.
- Use focused CSO/security review for OAuth, JWT, refresh tokens, admin actions,
  secrets, deployment security, AI prompts, external URLs, and user-generated
  content moderation.

## Final Decision

Proceed with implementation using the next PR order above. The immediate next
slice should be Admin report/status Web UI because it connects already completed
backend admin/report work to a visible MVP workflow.
