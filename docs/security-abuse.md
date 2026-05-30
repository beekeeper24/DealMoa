# Security And Abuse

## Reports

Reports never automatically hide or down-rank content. They create admin review priority only.

## Submissions

- Login required.
- Daily limit.
- Duplicate URL checks.
- AI first-pass review.
- Admin approval before publishing.

## Verified Reviews

- Login required.
- Purchase record or receipt/order image.
- AI first-pass review.
- Admin approval before `VERIFIED`.
- Only verified reviews are strong AI purchase-check evidence.

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
- Browser-readable storage may hold OAuth `state` only; refresh tokens and bearer access tokens must not be exposed there.

## External URLs

- Validate URLs.
- Use allowlist/blocklist policy.
- Do not expose unapproved suspicious links.

## AI

- Rate-limit AI requests.
- Validate structured outputs.
- Never let AI approve publishing by itself.

## Admin

- Enforce `ADMIN` role.
- Keep audit logs for admin actions.
