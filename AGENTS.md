# AGENTS.md

## Harness Routing

Use the harness stack automatically by task type and risk. Do not ask the user to name a harness for ordinary work.

- Keep simple tasks in the main Codex flow. Do not add orchestration overhead for trivial edits, typo fixes, formatting-only changes, clear one-file fixes, straightforward scaffolding, or implementation already covered by fixed `docs/` decisions.
- Codex should use the main flow by default and choose OMX team, Codex native subagents, or other orchestration only when task shape and risk make parallel work useful.
- The user does not need to explicitly request sub-agents; Codex may use them for clearly separable implementation, research, review, or verification tracks that do not create file conflicts.
- If the active runtime blocks sub-agent or team execution, state the constraint briefly and continue with the best available harness fallback.
- Use OMX `deep-interview` when requirements, boundaries, or acceptance criteria are unclear.
- Use Superpowers `brainstorming` only for new product decisions, UX decisions, behavior changes, or scope changes not already covered by `docs/`.
- Use Superpowers `writing-plans` before non-trivial implementation plans, especially when multiple apps, infra services, or data flows are affected.
- Use Superpowers `test-driven-development` for ranking logic, authentication, authorization, token handling, error-code behavior, event processing, data migrations, concurrency, state transitions, and high-risk backend behavior.
- Use Superpowers `systematic-debugging` when the bug cause is unclear.
- Use Superpowers `verification-before-completion` before claiming completion on meaningful work.
- Use gstack `cso` / `/cso` for focused security review on OAuth2, JWT, refresh tokens, secrets, `.env` handling, admin authorization, Kafka event handling, notification fan-out, external URLs, AI prompt handling, and user-generated content moderation.
- Use Compound Engineering only for important lessons or when the same mistake repeats at least three times. Keep these notes separate from human-facing work logs.

## Harness Composition

Use harnesses together when they cover different parts of the work. The default question is not "did the user ask for a harness?" but "which harness combination reduces risk or improves throughput for this task?"

- Do not run multiple planning harnesses by default. Pick one lead planning harness, then add other harnesses only for distinct follow-up roles such as parallel execution, security review, verification, or learning capture.
- Use OMX-led planning when the main uncertainty is requirements, boundaries, acceptance criteria, or how to split work across agents.
- Use Superpowers-led planning when the main uncertainty is engineering method: TDD shape, implementation sequence, debugging discipline, or a concrete written plan.
- If both OMX and Superpowers could apply, choose the lighter one that answers the blocking question. Combining both is justified only when the second harness answers a different question, not when it repeats the same planning work.
- Simple direct work:
  - Use main Codex flow.
  - Examples: typo fixes, one-file docs edits, small config edits, obvious test expectation updates, basic folder scaffolding, simple health endpoints.
- Ambiguous requirements:
  - Use OMX `deep-interview` before implementation.
  - Stop once acceptance criteria, boundaries, and non-goals are clear.
- New feature or behavior change:
  - Use Superpowers `brainstorming` or `writing-plans` to shape the approach when the feature goal is clear enough to plan implementation.
  - Use OMX `deep-interview` first only when the feature goal, boundaries, or acceptance criteria are still unclear.
  - Use OMX team/orchestration or Codex native subagents if implementation, tests, docs, and review can be split safely.
  - Use main Codex for final integration and verification.
- High-risk backend logic:
  - Use Superpowers `test-driven-development`.
  - Prefer orchestration when independent test, implementation, and review tracks exist.
  - Applies to authentication, authorization, token handling, error-code behavior, ranking, data migration, concurrency, event idempotency, and state transitions.
- Superpowers TDD test design:
  - Do not stop at happy-path-only tests for meaningful backend behavior.
  - Include meaningful edge cases that affect correctness, security, state transitions, ranking results, event idempotency, or data consistency.
  - Do not add absurd, unrealistic, or low-value cases just to increase test count.
  - Split tests by feature behavior and unit boundary so each test has one clear reason to fail.
  - Prefer focused unit/use-case tests first, then add integration/e2e tests only where boundaries matter.
  - For simple scaffolding or trivial config changes, smoke checks may be enough.
- Unclear bug:
  - Use Superpowers `systematic-debugging`.
  - Add orchestration when one track can reproduce the issue while another inspects code/history/config.
- Security-sensitive change:
  - Use the appropriate implementation harness first.
  - Then run gstack `cso` / `/cso` for focused security review.
  - Applies to OAuth2, JWT, refresh tokens, secrets, deployment security, data exposure, admin authorization, notification fan-out, external URLs, AI prompt handling, and user-generated content moderation.
- Meaningful completed work:
  - Use Superpowers `verification-before-completion` before claiming completion.
  - Use Compound Engineering only when review or implementation reveals an important lesson, or when the same mistake has repeated at least three times and needs a prevention note.
  - Update Notion work logs for human-facing study/progress context when the work is meaningful.

OMX team/orchestration or Codex native subagents are preferred when at least two of these are true:

- there are 2+ independent workstreams;
- code changes span multiple modules or ownership boundaries;
- a separate reviewer can catch risk while implementation continues;
- external docs/research can run in parallel with local code reading;
- browser/runtime verification can run separately from code edits;
- the task has enough scope that orchestration overhead is smaller than the risk of serial blind spots.

Do not use orchestration when it would create file conflicts, duplicate the same investigation, or slow down a clear small fix.

## Execution Principles

- Work as a study partner for a new-grad backend developer: explain important engineering decisions briefly and keep the code structure learnable.
- Prefer simple, conventional FastAPI, SQLAlchemy, Next.js, Elasticsearch, Kafka, and Celery patterns before clever abstractions.
- Search and ranking are the core of this project; preserve clarity around scoring, indexing, analyzers, and measurement.
- Do not run every workflow every time.
- Choose the lightest safe workflow that covers the task risk.
- Check `git status` before edits when the directory is a git repository.
- Never revert existing user changes unless the user explicitly asks.
- Work from the current tree state; do not reset or discard user work.
- Verify meaningful edits with tests, lint, typecheck, build, focused runtime checks, or documented fallback verification.
- Keep commits scoped to one meaningful unit.

## Review And Learning Loop

For meaningful work, use this loop:

1. Route the task through the lightest suitable harness.
2. Implement or investigate.
3. Verify with tests, build, lint, typecheck, focused runtime checks, or documented fallback verification as appropriate.
4. Run gstack `cso` / `/cso` when the change affects OAuth2, authentication, authorization, secrets, `.env` handling, deployment security, data exposure, admin authorization, Kafka event handling, notification fan-out, external URLs, AI prompt handling, or user-generated content moderation.
5. Capture what should make the next similar task easier.

Learning notes split:

- The DealMoa Notion project page is an index page only. Keep this hierarchy: `작업일지 > DealMoa > DealMoa 인수인계 문서 / dated work-log pages`.
- The handoff/context document belongs in the `DealMoa 인수인계 문서` child page, not in the DealMoa project page body.
- Notion work logs are human-facing study, portfolio, and progress records. Create them as dated child pages directly under `DealMoa`. Do not create an intermediate folder page.
- Project learnings under `docs/learnings/` are for future Codex sessions: repeated gotchas, local conventions, architectural decisions, and verification rules.
- After meaningful work, create or update a dated child work-log page directly under `DealMoa` so a resumed session can quickly recover context without disturbing the project index or handoff page.

## Project Defaults

- Project name: `DealMoa` / `딜모아`.
- Local project path: `/home/beekeeper24/projects/DealMoa` in WSL Ubuntu; Windows UNC path is `\\wsl.localhost\Ubuntu\home\beekeeper24\projects\DealMoa`.
- GitHub repository is `beekeeper24/DealMoa`.
- Main branch is `main`; integration branch is `develop`.
- Monorepo apps: `apps/web`, `apps/api`, `apps/worker`, `apps/consumer`.
- Backend stack: FastAPI, Python, Pydantic, SQLAlchemy, Alembic.
- Frontend stack: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui.
- Python package/environment manager: `uv`.
- Frontend package manager: `pnpm`.
- Python version target: `3.12` unless a core dependency forces a downgrade.
- Database: PostgreSQL.
- Search: Elasticsearch with Nori analyzer, exact fields, ngram/search-as-you-type fields, synonym/alias handling, limited fuzzy fallback, and vector fields for AI search/recommendation.
- Queue/workers: Kafka for domain events; Celery + Redis for background jobs, crawling, AI review, embeddings, and scheduled work.
- Observability: Prometheus and Grafana.
- Load testing: JMeter.
- API style: REST.
- API prefix: `/api/v1`.
- OAuth providers: Google, Kakao, Naver from the first implementation pass.
- Social auth flow includes existing account login, signup completion, same-email account linking, provider connect/disconnect, JWT access token, refresh token rotation, and hashed refresh token storage.
- Environment strategy: root `.env` for local runtime, committed `.env.example` for required variable documentation, no committed secrets.
- Do not introduce Turborepo/Nx in the first scaffold. Add it only if command orchestration becomes painful.
- Commit messages should be written in Korean when the user asks for project commits, and each commit should represent one reviewable intent.

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
- AI purchase checks should primarily use price history, current deal/auction conditions, verified purchase reviews, specs, and alternatives. Do not summarize manipulable community public opinion as fact.

## API And Error Rules

- Routers and use cases should not raise FastAPI `HTTPException` for business errors.
- Use `DealMoaException -> DomainException -> ConcreteException` for business exceptions.
- Global FastAPI exception handlers convert project exceptions into the common error response shape.
- Error responses include stable `code`, user-facing Korean `message`, structured `details`, and `traceId`.
- Frontend behavior should branch on `code`, not on `message`.
- See `docs/api-error-handling.md` before changing error-code behavior.

## Ranking Rules

- Hot-deal ranking:
  - `HotDealScore = PriceScore 50 + InterestScore 30 + FreshnessScore 10 + TrustScore 10`.
  - Trust can gate or exclude low-quality candidates after admin/status validation.
  - Reports do not directly affect score until an admin action changes status.
- Home auction ranking:
  - `AuctionActivityScore = BidActivity 45 + UniqueBidder 20 + ViewMomentum 15 + Interest 10 + EndingSoon 5 + Trust 5`.
  - Home should show auctions that are actually active, not hidden opportunity deals.
- General product search:
  - Text relevance dominates. Exact model/brand matches must not be displaced by popularity or price.
  - Use Nori, exact fields, alias/synonym, ngram/search-as-you-type, and limited fuzzy fallback.
- AI search:
  - Use structured `SearchIntent`, Pydantic validation, allowed filters only, vector search, BM25, and explanatory ranking.

## Async Boundaries

- FastAPI handles request validation, auth, DB transactions, REST orchestration, and outbox event creation.
- Kafka carries initial domain events: `deal.created`, `auction.created`, and `product.updated`.
- Later Kafka events can include `auction.bid.placed`, `favorite.product.created`, `review.verified`, and `submission.approved`.
- Kafka consumers handle Elasticsearch indexing and interest-based notification candidate creation.
- Celery handles initial tasks: `crawl_hot_deals_mock`, `ai_review_submission_mock`, and `rebuild_search_index`.
- Later Celery tasks can include real crawler jobs, receipt verification, embedding generation, price history snapshots, and notification batches.
- Do not make Kafka and Celery produce the same side effect without an idempotency key or deduplication strategy. Kafka is for events; Celery is for jobs.

## Documentation

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
  - `docs/api-error-handling.md`
  - `docs/ai-assistant.md`
  - `docs/observability.md`
  - `docs/performance.md`
  - `docs/security-abuse.md`

## Git Flow

- Use Git Flow-style branch management.
- `main` is the stable release branch. Do not commit or push routine work directly to `main`.
- `develop` is the integration branch. Merge into `develop` only after a coherent feature/MVP slice is locally verified and PR-ready.
- Create feature branches from `develop`.
- A feature branch represents one coherent deliverable, such as Milestone 1 scaffolding, OAuth login, search indexing, ranking, notifications, or admin review workflow. Do not open and merge a PR merely because one intermediate task ended.
- Keep incremental checkpoint commits on the same feature branch while that deliverable is still in progress.
- Split a large milestone into multiple PRs only when each PR leaves `develop` coherent, runnable, and understandable on its own.
- Use branch prefixes: `feature/...`, `fix/...`, `test/...`, `refactor/...`, `chore/...`, `docs/...`, `release/...`, and `hotfix/...`.
- Do not use a `codex/` branch prefix.
- Push work branches and `develop` as needed. Promote to `main` only through an intentional release step.
- Split commits by reviewable intent, not by tool run.
- When the user asks to commit during an active feature branch, commit the verified checkpoint and push the branch if useful; do not open or merge a PR unless the feature/MVP slice is ready or the user explicitly asks for a PR.
- When the feature/MVP slice is ready for integration, treat the default completion path as:
  1. commit all verified work on the feature branch;
  2. push the feature branch;
  3. open or update a PR into `develop`;
  4. mark the PR ready after local verification and any required CI/review checks;
  5. merge it into `develop`;
  6. sync local `develop`.
- Stop at a draft/open PR only when the user explicitly asks for review-only handling, when verification is incomplete, or when CI/conflicts/blockers make merge unsafe. State the blocker and next activation step clearly.

## Reporting

Final responses should briefly report:

- what changed;
- what verification ran;
- what learning or handoff note was updated;
- any follow-up activation step that still requires the user.
