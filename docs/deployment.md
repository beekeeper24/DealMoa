# Deployment Baseline

DealMoa deploys with Vercel for the web app and Railway for backend services.

This document is the deployment contract. Local development should mimic this contract with different values, not different application behavior.

Use `docs/release-readiness.md` as the step-by-step preparation checklist before
entering real Vercel/Railway values. It separates Vercel public env, Railway secrets,
OAuth provider setup, optional OpenAI activation, worker/consumer readiness, and stop
conditions.

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
AI_REVIEW_PROVIDER=mock
AI_ASSISTANT_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_REVIEW_MODEL=gpt-4o-mini
OPENAI_ASSISTANT_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=8
AI_REVIEW_USER_WINDOW_LIMIT=20
AI_REVIEW_USER_WINDOW_HOURS=24
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

Keep `AI_REVIEW_PROVIDER=mock` until provider cost controls, rate limits, and monitoring
are ready. When switching to `openai`, set `OPENAI_API_KEY` only in Railway secrets, not
in committed files.

Keep `AI_ASSISTANT_PROVIDER=mock` for the first deployment unless OpenAI budget and
monitoring are intentionally enabled. The assistant provider shares `OPENAI_API_KEY`,
`OPENAI_BASE_URL`, and `OPENAI_TIMEOUT_SECONDS`, and uses `OPENAI_ASSISTANT_MODEL`.

For the first public API deploy, prefer `API_METRICS_ENABLED=false` unless `/metrics` is
protected by Railway networking or another access-control layer.

## Railway Worker Settings

Create a separate Railway worker service when deployed Celery tasks should run.

Recommended settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/worker/Dockerfile`
- Public Networking: disabled unless metrics are intentionally protected

Required worker variables:

```text
DATABASE_URL=postgresql+psycopg://...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
AUCTION_ENDING_SOON_LOOKAHEAD_MINUTES=60
AUCTION_ENDING_SOON_BATCH_SIZE=100
AUCTION_ENDING_SOON_SCHEDULE_SECONDS=300
CRAWLER_SYSTEM_USER_ID=system-crawler
CRAWLER_SYSTEM_USER_EMAIL=crawler@dealmoa.local
CRAWLER_SYSTEM_USER_NICKNAME=DealMoa Crawler
CRAWLER_SOURCE_PROFILES=mock.example.com:trusted:allow
CRAWLER_SOURCE_PARSERS=mock.example.com:dealmoa_article
CRAWLER_LIVE_URLS=
CRAWLER_HTTP_TIMEOUT_SECONDS=5
CRAWLER_HTTP_MAX_BYTES=1048576
CRAWLER_MAX_URLS_PER_HOST=20
CRAWLER_USER_AGENT=DealMoaBot/0.1 (+https://<project-domain>/crawler)
WORKER_METRICS_ENABLED=false
WORKER_METRICS_PORT=9102
```

Keep `CRAWLER_LIVE_URLS` empty for the first deployment unless source hosts and parser
mappings have been reviewed.

## Railway Consumer Settings

Create consumer services when deployed Kafka event processing is ready. Search indexing
and notification generation use separate commands so they can be deployed as separate
Railway services if needed.

Recommended settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/consumer/Dockerfile`
- Public Networking: disabled unless metrics are intentionally protected
- Search indexing command: `uv run python -m consumer_app.main consume-search-index`
- Notification command: `uv run python -m consumer_app.main consume-notifications`

Required consumer variables:

```text
DATABASE_URL=postgresql+psycopg://...
KAFKA_BOOTSTRAP_SERVERS=<broker-host:port>
KAFKA_DOMAIN_EVENTS_TOPIC=dealmoa.domain-events
KAFKA_SEARCH_INDEX_GROUP_ID=dealmoa-search-indexer
KAFKA_NOTIFICATION_GROUP_ID=dealmoa-notification-generator
ELASTICSEARCH_URL=https://...
CONSUMER_POLL_INTERVAL_SECONDS=1
CONSUMER_BATCH_SIZE=100
CONSUMER_METRICS_ENABLED=false
CONSUMER_METRICS_PORT=9101
```

If Kafka is not provisioned for the first deployment, keep consumer services disabled and
use admin reindex plus direct API smoke paths for the first release check.

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
- Railway healthchecks: https://docs.railway.com/reference/healthchecks
- Railway config/build settings including Dockerfile path and start command: https://docs.railway.com/reference/config-as-code
