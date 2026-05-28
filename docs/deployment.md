# Deployment Baseline

DealMoa deploys with Vercel for the web app and Railway for backend services.

This document is the deployment contract. Local development should mimic this contract with different values, not different application behavior.

## Service Ownership

| Runtime | Platform | Source | Notes |
| --- | --- | --- | --- |
| Web | Vercel | `apps/web` | Next.js App Router app. |
| API | Railway | repo root + `apps/api/Dockerfile` | FastAPI app, listens on Railway `PORT`. |
| PostgreSQL | Railway | managed service | Source-of-truth database. |
| Redis | Railway | managed service | Refresh/session-adjacent jobs and later Celery broker/cache. |
| Elasticsearch | Railway or external managed service | service URL only | Must expose an HTTP URL reachable from the API service. |
| Worker | Railway later | `apps/worker` | Celery runtime after worker slice exists. |
| Consumer | Railway later | `apps/consumer` | Kafka/Elasticsearch sync runtime after event slice exists. |

Docker Compose is local tooling only. It is used for local infra, smoke tests, demos, and onboarding.

## Vercel Web Settings

Create a Vercel project for `apps/web`.

Recommended settings:

- Root Directory: `apps/web`
- Framework Preset: Next.js
- Install Command: Vercel default for the monorepo package manager unless the project import requires an override.
- Build Command: Vercel default Next.js build unless the project import requires an override.
- Output Directory: Vercel default for Next.js

Required environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<railway-api-domain>/api/v1
```

Do not put API secrets, OAuth client secrets, JWT secrets, database URLs, Redis URLs, or Elasticsearch URLs in Vercel web env. The browser app only needs the public API base URL.

## Railway API Settings

Create a Railway service for the API.

Recommended settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/api/Dockerfile`
- Public Networking: enabled for the API service
- Healthcheck Path: `/health`

The API container listens on `${PORT:-8000}`. Railway should provide `PORT`; local Docker falls back to `8000`.

Required Railway API variables:

```text
API_ENV=production
API_PROJECT_NAME=DealMoa API
API_V1_PREFIX=/api/v1
API_CORS_ORIGINS=https://<vercel-domain>
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
ELASTICSEARCH_URL=https://...
JWT_SECRET_KEY=<at-least-32-random-bytes>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=14
AUTH_REFRESH_COOKIE_NAME=dm_refresh_token
AUTH_REFRESH_COOKIE_SECURE=true
AUTH_REFRESH_COOKIE_SAMESITE=none
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
OAUTH_KAKAO_CLIENT_ID=...
OAUTH_KAKAO_CLIENT_SECRET=...
OAUTH_NAVER_CLIENT_ID=...
OAUTH_NAVER_CLIENT_SECRET=...
```

Use `AUTH_REFRESH_COOKIE_SAMESITE=none` with `AUTH_REFRESH_COOKIE_SECURE=true` when the Vercel web domain and Railway API domain are different sites. Local development can use `lax` and `false`.

## OAuth Redirect URLs

Register callback URLs per provider.

Local:

```text
http://localhost:3000/auth/callback/google
http://localhost:3000/auth/callback/kakao
http://localhost:3000/auth/callback/naver
```

Production:

```text
https://<vercel-domain>/auth/callback/google
https://<vercel-domain>/auth/callback/kakao
https://<vercel-domain>/auth/callback/naver
```

The browser callback page exchanges the provider `code` with the Railway API. Refresh tokens remain in the API-owned HttpOnly cookie.

## Database Migrations

Migrations are explicit release operations.

Run before or during Railway deploy:

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
```

Do not run Alembic automatically inside the API web process. Later, Railway pre-deploy commands or a one-off Railway job can own migration execution once the first real deployment is configured.

## Local Development Parity

Local `.env` values should use the same variable names as production whenever possible.

Local web:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Local API:

```text
API_ENV=local
API_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3100
AUTH_REFRESH_COOKIE_SECURE=false
AUTH_REFRESH_COOKIE_SAMESITE=lax
```

Docker Compose may still accept `WEB_PUBLIC_API_BASE_URL` as a backward-compatible local alias, but Vercel uses `NEXT_PUBLIC_API_BASE_URL`.

## Promotion Checklist

Before promoting a slice toward deployment:

- API tests, typecheck, and lint pass.
- Web tests, typecheck, lint, and build pass.
- `docker compose --profile core config --quiet` passes.
- `.env.example` documents every newly required runtime variable.
- No production secret is committed.
- OAuth callback URLs and CORS origins match the active Vercel/Railway domains.

## References

- Vercel monorepo root-directory deployment: https://vercel.com/docs/monorepos
- Railway monorepo deployment and service root settings: https://docs.railway.com/guides/monorepo
- Railway config/build settings including Dockerfile path and start command: https://docs.railway.com/reference/config-as-code
