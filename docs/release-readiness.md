# Release Readiness

This checklist prepares DealMoa for the first Vercel/Railway deployment after feature
MVP completion. It is not a deployment log. Fill these values in the platform dashboards
or secret managers only; do not commit real secrets.

## Deployment Inputs To Prepare

Prepare these before the first deployment pass:

| Input | Required for first deploy | Where it is used |
| --- | --- | --- |
| Vercel web domain | Yes | OAuth callbacks, API CORS, cookie site behavior |
| Railway API domain | Yes | `NEXT_PUBLIC_API_BASE_URL`, OAuth code exchange target |
| Railway PostgreSQL URL | Yes | `DATABASE_URL` |
| Railway Redis URL | Yes | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| Elasticsearch HTTP URL reachable from Railway | Yes | `ELASTICSEARCH_URL` for API and consumer |
| JWT secret, at least 32 random bytes | Yes | `JWT_SECRET_KEY` |
| Google OAuth client id and secret | Yes for Google login | API OAuth provider config |
| Kakao OAuth client id and secret | Yes for Kakao login | API OAuth provider config |
| Naver OAuth client id and secret | Yes for Naver login | API OAuth provider config |
| OpenAI API key | No for first deploy if providers stay `mock` | Required only when `AI_REVIEW_PROVIDER=openai` or `AI_ASSISTANT_PROVIDER=openai` |

## Vercel Web Project

Create a Vercel project rooted at `apps/web`.

Recommended project settings:

- Root Directory: `apps/web`
- Framework Preset: Next.js
- Install Command: Vercel default unless the import flow requires an override
- Build Command: Vercel default unless the import flow requires an override
- Output Directory: Vercel default for Next.js

Required Vercel environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://<railway-api-domain>/api/v1
```

Do not add these to Vercel web env:

- `DATABASE_URL`
- `REDIS_URL`
- `ELASTICSEARCH_URL`
- `JWT_SECRET_KEY`
- OAuth client secrets
- `OPENAI_API_KEY`
- Kafka/Celery service URLs

The web app runs in the browser. Any `NEXT_PUBLIC_*` variable is public by design.

## Railway API Service

Create a Railway service for the API.

Recommended service settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/api/Dockerfile`
- Public Networking: enabled
- Healthcheck Path: `/health`

Required Railway API variables:

```text
API_ENV=production
API_PROJECT_NAME=DealMoa API
API_V1_PREFIX=/api/v1
API_CORS_ORIGINS=https://<vercel-domain>
API_METRICS_ENABLED=false
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
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

Use `AUTH_REFRESH_COOKIE_SECURE=true` and `AUTH_REFRESH_COOKIE_SAMESITE=none` when the
Vercel web domain and Railway API domain are different sites. That is the expected first
deployment shape.

Set `API_METRICS_ENABLED=false` for the first public API deploy unless Railway networking
or another access-control layer protects `/metrics`. The metrics endpoint exposes route
names, status-code counts, latency buckets, and default Python/process metrics.

## Railway Worker Service

Create a separate Railway worker service only when background tasks should run in the
deployed environment. The first API deploy can happen without a public worker service,
but crawler tasks, scheduled auction-ending notifications, and Celery-backed admin
triggers need it.

Recommended service settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/worker/Dockerfile`
- Public Networking: disabled unless a metrics endpoint is intentionally protected
- Start Command: keep the Dockerfile default worker command unless Railway requires an override

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

Keep `CRAWLER_LIVE_URLS` empty for the first deployment unless the target source hosts,
parser mappings, and source profiles are intentionally reviewed. Do not expose worker
metrics publicly.

## Railway Consumer Service

Create a separate Railway consumer service only when deployed Kafka/event processing is
ready. The first API/web smoke can run without it, but deployed search-index freshness and
async notification generation need it.

Recommended service settings:

- Source: GitHub repository `beekeeper24/DealMoa`
- Root Directory: repository root
- Dockerfile Path: `apps/consumer/Dockerfile`
- Public Networking: disabled unless a metrics endpoint is intentionally protected
- Start Command for search indexing: `uv run python -m consumer_app.main consume-search-index`
- Start Command for notifications: `uv run python -m consumer_app.main consume-notifications`

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

If Railway Kafka is not provisioned for the first deployment, keep the consumer services
disabled and rely on admin reindex plus direct API flows for the initial smoke.

## OAuth Provider Console Setup

Create one production OAuth app per provider or add production callbacks to existing
apps.

Production redirect URLs:

```text
https://<vercel-domain>/auth/callback/google
https://<vercel-domain>/auth/callback/kakao
https://<vercel-domain>/auth/callback/naver
```

Provider values to give the Railway API service:

```text
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
OAUTH_KAKAO_CLIENT_ID=...
OAUTH_KAKAO_CLIENT_SECRET=...
OAUTH_NAVER_CLIENT_ID=...
OAUTH_NAVER_CLIENT_SECRET=...
```

Local callbacks remain:

```text
http://localhost:3000/auth/callback/google
http://localhost:3000/auth/callback/kakao
http://localhost:3000/auth/callback/naver
```

Do not use localhost callbacks as the only registered callback in production provider
apps.

## Optional OpenAI Provider Activation

The first deployment should keep:

```text
AI_REVIEW_PROVIDER=mock
AI_ASSISTANT_PROVIDER=mock
OPENAI_API_KEY=
```

Switch to OpenAI only after provider cost controls, monitoring, and budget expectations
are ready:

```text
AI_REVIEW_PROVIDER=openai
AI_ASSISTANT_PROVIDER=openai
OPENAI_API_KEY=<railway-secret>
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_REVIEW_MODEL=gpt-4o-mini
OPENAI_ASSISTANT_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=8
AI_REVIEW_USER_WINDOW_LIMIT=20
AI_REVIEW_USER_WINDOW_HOURS=24
```

Never put `OPENAI_API_KEY` in Vercel `NEXT_PUBLIC_*` variables or committed files.

## Migration And Seed Order

Before deployed smoke checks:

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
```

Then, if a demo dataset is needed:

```bash
python -m app.modules.demo_seed.cli --reindex
```

Run those against the deployed Railway database/API environment intentionally. Do not run
migrations automatically inside the API web process.

## First Deploy Stop Conditions

Stop and fix before public smoke if any of these are true:

- `.env`, OAuth secrets, JWT secret, database URLs, Redis URLs, Elasticsearch URLs, or
  OpenAI keys are staged for commit.
- `NEXT_PUBLIC_API_BASE_URL` points to localhost in Vercel production.
- `API_CORS_ORIGINS` does not include the active Vercel domain.
- OAuth provider apps do not include the active Vercel callback URLs.
- `AUTH_REFRESH_COOKIE_SECURE=false` or `AUTH_REFRESH_COOKIE_SAMESITE=lax` is used for
  split Vercel/Railway production domains.
- `/metrics`, worker metrics, or consumer metrics are publicly reachable without access
  control.
- `AI_REVIEW_PROVIDER=openai` or `AI_ASSISTANT_PROVIDER=openai` is enabled without an
  explicit budget and monitoring decision.
