# Security And Abuse

## Reports

Reports never automatically hide or down-rank content. They create admin review priority only.
Only an admin status decision, such as moving a deal or auction to `active`, `verified`,
`rejected`, or `blocked`, changes search visibility and status-derived trust.
- Report creation requires login.
- Duplicate open reports from the same user for the same deal/auction return the existing
  open report instead of creating another open queue item.
- Admin report review can mark a report `resolved` or `dismissed`.
- Admin report review can also include an explicit `targetStatus` decision to mutate the
  underlying deal/auction status in the same transaction; the report count itself never
  performs that mutation automatically.

## Submissions

- Login required.
- Duplicate `sourceUrl` checks in the MVP return the existing submission row.
- Submission `sourceUrl` accepts only `http` and `https` URLs at intake.
- AI first-pass review records reviewer-facing evidence only; it never publishes content.
- Mock crawler ingestion writes `pending_review` submissions only; it does not fetch live
  external pages or publish Product/Deal/Auction rows.
- Crawler source profiles must explicitly allow source hosts; unknown and blocked hosts
  are skipped before database writes.
- Live crawler URL fetching is disabled by default with an empty `CRAWLER_LIVE_URLS`.
- Live crawler URLs must pass source profiles before network access, then pass SSRF-safe
  DNS/IP checks, robots.txt policy, content-type checks, and response-size limits.
- Live fetched HTML must also pass `CRAWLER_SOURCE_PARSERS`; missing or unsupported parser
  mappings are skipped before submission validation or database writes.
- `CRAWLER_MAX_URLS_PER_HOST` limits same-host fetches within one live crawler task run;
  over-limit URLs are skipped before network fetch.
- Crawler task summaries are visible only through the admin-only crawler run log API and
  web page. These logs expose counts, skip reasons, and bounded failure fields, not
  fetched HTML.
- Manual crawler execution is admin-only and accepts only the allowlisted task names
  `crawl_hot_deals_mock` and `crawl_live_urls`. It does not accept arbitrary task names or
  per-request URLs, so live fetch targets remain controlled by `CRAWLER_LIVE_URLS` and
  worker-side source/parser/SSRF/rate-limit checks.
- The crawler system user is non-admin.
- Admin approval is required before Product, Deal, or Auction rows are created.
- Product matching suggestions are admin-only hints and never publish content by themselves.
- Admin approval may attach an offer to an existing Product with `targetProductId`; missing
  product IDs fail with `PRODUCT_NOT_FOUND`.
- Admin approval/rejection writes `admin_audit_logs`.
- Product discussion comments store deterministic moderation risk signals for admin
  priority only. Public discussion APIs do not expose risk fields, and risk signals do
  not automatically hide, delete, rank, or penalize comments/users.
- Distributed Redis-backed rate windows, production crawl scheduling, retry metadata,
  per-request crawler URL input, and automated duplicate cleanup are deferred security
  hardening items.

## Verified Reviews

- Login required.
- MVP proof data is a text receipt/order reference; receipt image upload and OCR are deferred.
- A non-empty proof reference is required for purchase verified review submission.
- A user can submit at most one verified review for the same product.
- A proof reference can be used only once.
- Normal MVP verified reviews publish immediately as `approved` after lightweight request
  validation. They do not call the AI review provider and do not consume AI review quota.
- Platform-risk or admin-flagged reviews move through post-publication moderation.
- Consumer report buttons for verified reviews are deferred in the MVP.
- Verified-review duplicate submit guards reject same-user/product duplicates and reused
  proof references before publish.
- Verified-review risk signals are deterministic admin priority fields only:
  off-platform contact language, repeated URLs, and blocked commercial spam terms. They
  do not automatically hide, reject, down-rank, or penalize reviews/users.
- Admin hide/restore/reject actions write `admin_audit_logs`.
- Public approved-review responses exclude internal user ids, proof references, AI review
  text, admin reviewer ids, and resolution notes.
- Only `approved` verified reviews are strong AI purchase-check evidence. `hidden`,
  `pending_review`, and `rejected` reviews are excluded from public evidence.

## Product Discussions

- Public discussion reads include visible comments only.
- Comment creation requires login.
- Public comment responses expose nickname and body only; they exclude internal user ids,
  moderation notes, reviewer ids, and hidden comments.
- Admin hide/restore requires `role = ADMIN` and writes `admin_audit_logs`.
- The web UI renders comment bodies as plain React text, not HTML.
- Discussion content is not used as AI purchase-check evidence, and comment volume does
  not affect ranking/trust scores in this slice.

## Favorites

- `unique(user_id, target_type, target_id)`.
- Product, deal, and auction favorites are distinct targets.

## Auth

- OAuth login issues DealMoa-owned access and refresh tokens.
- Access tokens are JWTs and must be signed with `JWT_SECRET_KEY`.
- `JWT_SECRET_KEY` must not be committed and should be at least 32 bytes in local/dev examples.
- Refresh tokens are opaque, transported only as HttpOnly cookies, and stored only as HMAC-SHA256 hashes.
- Refresh token use rotates the token and revokes the previous token.
- Logout revokes the refresh token from the HttpOnly cookie and deletes the cookie.
- Bearer-token failures use stable auth error codes, not framework-default response shapes.
- OAuth `state` is supplied by the client in the MVP; later full-stack auth should move state persistence to Redis or another server-side short-lived store.
- The web app keeps access tokens in React memory only and restores sessions through `POST /auth/token/refresh` with the HttpOnly refresh cookie.
- The web app root owns auth state through `AuthSessionProvider`; child components must consume that shared context instead of independently refreshing sessions.
- Browser-readable storage may hold OAuth `state` only; refresh tokens and bearer access tokens must not be exposed there.
- My Page contribution history uses only `/me/submissions`; it must not call admin
  submission APIs or expose another user's submissions.

## External URLs

- Validate URLs.
- Use allowlist/blocklist policy.
- Do not expose unapproved suspicious links.
- User-submitted source URLs remain review-queue data until admin approval. The first
  web admin queue opens source URLs in a new tab with `rel="noreferrer"`.
- Crawler source allowlists are host based in the worker. They are not a substitute for
  SSRF checks; both must pass before live crawler ingestion.
- The live crawler blocks non-HTTP schemes, URL userinfo, private/reserved DNS results,
  robots.txt disallowed paths, non-HTML responses, and over-limit response bodies.
- The live crawler connects to the validated resolved IP while retaining the original
  host for Host/SNI, instead of allowing the HTTP client to resolve the host again.
- Robots.txt fetch failures are treated conservatively as skips. Redirects are not
  followed in the first live crawler pass.
- Parsed crawler content is still untrusted candidate data and remains subject to AI
  first-pass review plus admin approval.
- Source parser mappings do not make a source trusted; they only select which bounded
  parser may interpret a host's fetched HTML.

## AI

- Rate-limit AI requests.
- Validate structured outputs.
- Never let AI approve publishing by itself.
- AI search must convert user text or future model output into a validated `SearchIntent`
  before building Elasticsearch queries.
- AI search may use only allowlisted target types and filters; raw user text or model
  text must never become query DSL.
- AI assistant supports mock and OpenAI providers. OpenAI assistant output must use
  Structured Outputs and Pydantic validation. Invalid output, provider errors, timeouts,
  or missing API keys fall back to the mock provider.
- Purchase-check evidence uses approved verified reviews only and does not expose proof
  references, AI review reasoning, or admin moderation notes.
- Purchase-check provider input excludes proof references, admin notes, AI review
  reasoning, hidden/rejected/pending reviews, discussion text, and private user ids.
- AI first-pass review supports mock and OpenAI providers. OpenAI output must use
  Structured Outputs, is validated with Pydantic, and can only produce allowlisted
  `aiDecision` values.
- Provider failures or invalid output fall back to `needs_admin_review`; AI output never
  changes publish status.
- Verified-review `proofReference` is internal proof metadata and is not sent to the AI
  review provider in the current slice. Receipt image OCR remains deferred.
- User-triggered AI first-pass review calls are limited by
  `AI_REVIEW_USER_WINDOW_LIMIT` per `AI_REVIEW_USER_WINDOW_HOURS`, backed by
  PostgreSQL `ai_review_usage_events`. Normal verified-review auto-publish does not use
  this quota because it does not call AI.
- Real provider production use still needs richer abuse logging and provider-level
  monitoring before launch.

## Admin

- Enforce `ADMIN` role.
- Keep audit logs for admin actions.
- The first admin status APIs require bearer auth, fetch the current user from the database,
  and allow only `role = ADMIN`.
- Status changes write immutable `admin_audit_logs` rows with actor, target, previous status,
  new status, reason, and timestamps.
- Status-change events carry only offer IDs, status transition metadata, actor user ID, and
  reason; downstream consumers reload canonical offer state from PostgreSQL.
