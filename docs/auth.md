# Auth MVP

## Scope

Auth MVP fixes the backend authentication baseline before favorites and notifications.

Included:

- OAuth authorization URL generation for Google, Kakao, and Naver.
- OAuth authorization-code callback exchange boundary.
- Web login entry and callback route for Google, Kakao, and Naver.
- User and OAuth account persistence.
- DealMoa-owned JWT access token issuance.
- Opaque refresh token issuance, HttpOnly cookie transport, hashing, storage, rotation, and logout revocation.
- Authenticated current-user lookup with `Authorization: Bearer <accessToken>`.

Not included:

- Provider account disconnect.
- Admin role management.
- Favorites and notifications.
- OAuth state persistence. In this MVP, the client supplies and verifies `state`; later server-side state storage can move into Redis or a short-lived signed state table.

## Routes

Base prefix is `/api/v1`.

```http
GET /api/v1/auth/oauth/{provider}/authorize-url?redirectUri=...&state=...
POST /api/v1/auth/oauth/{provider}/callback
POST /api/v1/auth/token/refresh
POST /api/v1/auth/logout
GET /api/v1/auth/me
```

Web callback routes:

```http
GET /auth/callback/google
GET /auth/callback/kakao
GET /auth/callback/naver
```

Supported `provider` values:

- `google`
- `kakao`
- `naver`

## Token Policy

- Access tokens are JWTs signed with `JWT_SECRET_KEY`.
- Access tokens contain `sub`, `iat`, `exp`, and `typ=access`.
- Refresh tokens are opaque random strings.
- Refresh tokens are sent to the browser only through the `dm_refresh_token` HttpOnly cookie.
- Only refresh token hashes are stored in PostgreSQL.
- Refresh token use rotates the token: the previous token is revoked and a new one is issued.
- Logout revokes the refresh token from the HttpOnly cookie and deletes that cookie.
- The web MVP stores the returned access token and user in `sessionStorage`.
- OAuth `state` is provider-scoped and stored in `sessionStorage` until the callback consumes it once.

## Environment Variables

Canonical OAuth variable names:

```env
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
OAUTH_KAKAO_CLIENT_ID=...
OAUTH_KAKAO_CLIENT_SECRET=...
OAUTH_NAVER_CLIENT_ID=...
OAUTH_NAVER_CLIENT_SECRET=...
```

The API also accepts the `OAUTH2_...` prefix aliases for local convenience, for example `OAUTH2_GOOGLE_CLIENT_ID`.

Refresh cookie variables:

```env
AUTH_REFRESH_COOKIE_NAME=dm_refresh_token
AUTH_REFRESH_COOKIE_SECURE=false
AUTH_REFRESH_COOKIE_SAMESITE=lax
```

Use `AUTH_REFRESH_COOKIE_SECURE=true` on HTTPS environments.

Provider console redirect URI examples for local web development:

```text
http://localhost:3000/auth/callback/google
http://localhost:3000/auth/callback/kakao
http://localhost:3000/auth/callback/naver
```

## Response Shape

Token response:

```json
{
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "nickname": "Deal User",
    "role": "USER"
  },
  "accessToken": "jwt",
  "tokenType": "Bearer"
}
```

Current user response:

```json
{
  "id": "user-id",
  "email": "user@example.com",
  "nickname": "Deal User",
  "role": "USER"
}
```

## Provider Endpoints

The MVP adapter uses these provider endpoints:

| Provider | Authorization | Token | Profile |
| --- | --- | --- | --- |
| Google | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `https://openidconnect.googleapis.com/v1/userinfo` |
| Kakao | `https://kauth.kakao.com/oauth/authorize` | `https://kauth.kakao.com/oauth/token` | `https://kapi.kakao.com/v2/user/me` |
| Naver | `https://nid.naver.com/oauth2.0/authorize` | `https://nid.naver.com/oauth2.0/token` | `https://openapi.naver.com/v1/nid/me` |
