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
- Mock AI first-pass review records `needs_admin_review`; it never publishes content.
- Admin approval is required before Product, Deal, or Auction rows are created.
- Product matching suggestions are admin-only hints and never publish content by themselves.
- Admin approval may attach an offer to an existing Product with `targetProductId`; missing
  product IDs fail with `PRODUCT_NOT_FOUND`.
- Admin approval/rejection writes `admin_audit_logs`.
- Real rate limits, URL allowlist/blocklist, and automated duplicate cleanup are deferred
  security hardening items.

## Verified Reviews

- Login required.
- MVP proof data is a text receipt/order reference; receipt image upload and OCR are deferred.
- Mock AI first-pass review records `needs_admin_review`; it never publishes content.
- Admin approval is required before a review is publicly visible.
- Admin approval/rejection writes `admin_audit_logs`.
- Public approved-review responses exclude internal user ids, proof references, AI review
  text, admin reviewer ids, and resolution notes.
- Only verified reviews are strong AI purchase-check evidence.

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

## External URLs

- Validate URLs.
- Use allowlist/blocklist policy.
- Do not expose unapproved suspicious links.
- User-submitted source URLs remain review-queue data until admin approval. The first
  web admin queue opens source URLs in a new tab with `rel="noreferrer"`.

## AI

- Rate-limit AI requests.
- Validate structured outputs.
- Never let AI approve publishing by itself.
- AI search must convert user text or future model output into a validated `SearchIntent`
  before building Elasticsearch queries.
- AI search may use only allowlisted target types and filters; raw user text or model
  text must never become query DSL.
- Purchase-check evidence uses approved verified reviews only and does not expose proof
  references, AI review reasoning, or admin moderation notes.
- The first AI assistant implementation is deterministic mock logic. Real provider
  integration must add cost controls, prompt/output validation, and abuse logging before
  production use.

## Admin

- Enforce `ADMIN` role.
- Keep audit logs for admin actions.
- The first admin status APIs require bearer auth, fetch the current user from the database,
  and allow only `role = ADMIN`.
- Status changes write immutable `admin_audit_logs` rows with actor, target, previous status,
  new status, reason, and timestamps.
- Status-change events carry only offer IDs, status transition metadata, actor user ID, and
  reason; downstream consumers reload canonical offer state from PostgreSQL.
