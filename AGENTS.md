# AGENTS.md

## Harness Routing

Use the lightest harness that reduces risk or improves throughput. Do not ask the user to name a harness for ordinary work.

- Use normal Codex flow for simple edits, one-file docs changes, formatting-only changes, and clear small fixes.
- Use Superpowers `brainstorming` for new features, product decisions, UX decisions, and behavior changes that need design choices.
- Use Superpowers `writing-plans` before implementation plans for non-trivial work.
- Use Superpowers `test-driven-development` for ranking logic, authentication, authorization, event processing, data migrations, concurrency, and high-risk backend behavior.
- Use Superpowers `systematic-debugging` when the cause of a bug is unclear.
- Use Superpowers `verification-before-completion` before claiming completion on meaningful work.
- Use OMX or Codex native subagents only when work can be split into independent implementation, research, review, or verification tracks without file conflicts.
- If the active runtime blocks a harness or sub-agent path, state the constraint briefly and continue with the best available fallback.
- Use focused security review for OAuth2, JWT, refresh tokens, secrets, admin authorization, Kafka event handling, notification fan-out, external URLs, AI prompt handling, and user-generated content moderation.

## Execution Principles

- Work as a study partner for a new-grad backend developer: explain important engineering decisions briefly and keep the code structure learnable.
- Prefer simple, conventional FastAPI, SQLAlchemy, Next.js, Elasticsearch, Kafka, and Celery patterns before clever abstractions.
- Search and ranking are the core of this project; preserve clarity around scoring, indexing, analyzers, and measurement.
- Check `git status` before edits when the directory is a git repository.
- Never revert existing user changes unless the user explicitly asks.
- Work from the current tree state; do not reset or discard user work.
- Verify meaningful edits with tests, lint, typecheck, build, focused runtime checks, or documented fallback verification.
- Keep commits scoped to one meaningful unit.

## Project Defaults

- Project name: `DealMoa` / `딜모아`.
- Product concept: Korean hot-deal and auction discovery platform focused on search, ranking, alerts, and AI-assisted purchase checks.
- Backend stack: FastAPI, Python, Pydantic, SQLAlchemy, Alembic.
- Frontend stack: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui.
- Database: PostgreSQL.
- Search: Elasticsearch with Nori analyzer, exact fields, ngram/search-as-you-type fields, synonym/alias handling, limited fuzzy fallback, and vector fields for AI search/recommendation.
- Queue/workers: Kafka for domain events; Celery + Redis for command-style background jobs, crawling, AI review, embeddings, and scheduled work.
- Observability: Prometheus and Grafana.
- Load testing: JMeter.
- API style: REST.
- API prefix: `/api/v1`.
- OAuth providers: Google, Kakao, Naver from the first implementation pass.
- Social auth flow includes existing account login, signup completion, same-email account linking, provider connect/disconnect, JWT access token, refresh token rotation, and hashed refresh token storage.

## Domain Rules

- `Product` is the stable product identity.
- `Deal` is a specific hot-deal offer attached to a product.
- `Auction` is a specific auction listing attached to a product.
- Basic search is product-name, brand, model, category, and spec focused. It does not use vector search by default.
- AI search uses structured intent extraction, Elasticsearch filters, BM25, vector search, and ranking explanation.
- Product favorites trigger alerts for new related deals and auctions.
- Deal favorites are saved items and ranking signals.
- Auction favorites are saved items, auction activity signals, and ending-soon alert targets.
- Reports never automatically hide or down-rank content. They create an admin review priority signal only.
- User submissions and verified reviews require AI first-pass review plus admin approval. No automatic publishing.
- AI purchase checks should primarily use price history, current deal/auction conditions, verified purchase reviews, specs, and alternatives. Do not summarize manipulable community “public opinion” as fact.

## Ranking Rules

- Hot-deal ranking:
  - `HotDealScore = PriceScore 50 + InterestScore 30 + FreshnessScore 10 + TrustScore 10`.
  - Trust can gate or exclude low-quality candidates after admin/status validation.
  - Reports do not directly affect score until an admin action changes status.
- Home auction ranking:
  - `AuctionActivityScore = BidActivity 45 + UniqueBidder 20 + ViewMomentum 15 + Interest 10 + EndingSoon 5 + Trust 5`.
  - Home should show auctions that are actually active, not hidden “opportunity” deals.
- General product search:
  - Text relevance dominates. Exact model/brand matches must not be displaced by popularity or price.
  - Use Nori, exact fields, alias/synonym, ngram/search-as-you-type, and limited fuzzy fallback.
- AI search:
  - Use structured `SearchIntent`, Pydantic validation, allowed filters only, vector search, BM25, and explanatory ranking.

## Async Boundaries

- FastAPI handles request validation, auth, DB transactions, REST orchestration, and outbox event creation.
- Kafka carries domain events such as `deal.created`, `auction.created`, `product.updated`, `favorite.created`, and `review.verified`.
- Kafka consumers handle Elasticsearch indexing, notification generation, and ranking updates.
- Celery handles crawling, AI review, embedding generation, scheduled checks, and long-running Python jobs.
- Do not make Kafka and Celery produce the same side effect. Kafka is for events; Celery is for jobs.

## Notion And Documentation

- Human-facing work logs live under `작업일지 > DealMoa`.
- `작업일지 > DealMoa` is an index page.
- The handoff/context document belongs in a `DealMoa 인수인계 문서` child page.
- Dated work logs should be direct child pages under `DealMoa`.
- Local project docs belong in `docs/`.
- Maintain at least:
  - `docs/planning.md`
  - `docs/handoff.md`
  - `docs/search-ranking.md`
  - `docs/architecture.md`
  - `docs/ai-assistant.md`
  - `docs/observability.md`
  - `docs/performance.md`
  - `docs/security-abuse.md`

## Git Flow

- Use Git Flow-style branch management once the repository is initialized.
- `main` is stable release.
- `develop` is integration.
- Create feature branches from `develop`.
- Use branch prefixes: `feature/...`, `fix/...`, `test/...`, `refactor/...`, `chore/...`, `docs/...`, `release/...`, `hotfix/...`.
- Do not use a `codex/` branch prefix.
- Split commits by reviewable intent.

## Reporting

Final responses should briefly report:

- what changed;
- what verification ran;
- what Notion/local handoff note was updated;
- any follow-up activation step that still requires the user.
