# DealMoa Handoff

## Current Status

The project is in planning/setup. The active working path is:

```text
\\wsl.localhost\Ubuntu\home\beekeeper24\projects\DealMoa
```

Repository:

```text
https://github.com/beekeeper24/DealMoa.git
```

Current branch is `develop`. The initial planning baseline has already been pushed to GitHub. The current local work is documentation hardening before scaffolding.

## Fixed Decisions

- Project name: `딜모아` / `DealMoa`.
- Main portfolio axis: search/recommendation backend, not ordinary shopping CRUD.
- Monorepo apps: `apps/web`, `apps/api`, `apps/worker`, `apps/consumer`.
- Frontend package manager: `pnpm`.
- Python package/environment manager: `uv`.
- Python target: `3.12` unless a core dependency forces downgrade.
- Environment strategy: root `.env`, committed `.env.example`, no committed secrets.
- Architecture style: practical feature-module Clean/Hexagonal style.
- Domain model: Product-centered. Deals, auctions, reviews, discussions, price history, and favorites attach to products.
- API style: REST, `/api/v1`, resource URLs, cursor pagination by default.
- Error handling: `DealMoaException -> DomainException -> ConcreteException`; global FastAPI handlers convert exceptions to consistent error responses.
- Search: PostgreSQL source of truth, Elasticsearch read models.
- Elasticsearch indexes: `products_v1`, `deals_v1`, `auctions_v1`; unified/AI search uses multi-search.
- Korean search: Nori analyzer from the first Elasticsearch setup.
- General search: text relevance first, no vector by default.
- AI search: search-bar-side AI button, structured intent, filters, BM25, vector candidates, explanation.
- Kafka: domain event stream.
- Celery + Redis: long-running/scheduled Python jobs.
- Initial Kafka events: `deal.created`, `auction.created`, `product.updated`.
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
- `docs/search-ranking.md`: ranking and search decisions.
- `docs/ai-assistant.md`: AI search and purchase assistant decisions.
- `docs/performance.md`: JMeter and Playwright verification direction.
- `docs/observability.md`: Prometheus/Grafana direction.
- `docs/security-abuse.md`: abuse/security guardrails.

## Next Activation Steps

1. Review `AGENTS.md` against the fixed DealMoa plan.
2. Create a Milestone 1 branch.
3. Scaffold the project structure.
4. Add root `.env.example`.
5. Configure `uv` and `pnpm` workspaces.
6. Add Docker Compose `core` profile.
7. Add FastAPI health API.
8. Add Next.js shell.
9. Add initial CI.

## Milestone 1 Scope

- Monorepo folder structure.
- `uv` / `pnpm` workspace setup.
- Root `.env.example`.
- Docker Compose `core` profile.
- FastAPI app with health endpoint.
- Next.js app shell.
- PostgreSQL, Redis, Elasticsearch + Nori in local infra.
- GitHub Actions CI with backend/frontend lightweight checks.

## Cautions

- Do not commit `.env` or real OAuth/JWT secrets.
- Do not implement direct checkout/payment flows.
- Do not make AI a floating chatbot; use search-side entry points.
- Do not let report counts directly hide or down-rank content.
- Do not use FastAPI `HTTPException` inside domain/use case code for business errors.
- Do not introduce Turborepo/Nx in the first scaffold.
