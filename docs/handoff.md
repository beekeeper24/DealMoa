# DealMoa Handoff

## Current Status

The project is in planning/setup. The intended project folder name is `DealMoa`, but the active Codex Desktop session currently holds the original `새 폴더` directory open, so Windows refused an in-place rename. Rename after closing/reopening the session or from an external terminal when the directory is no longer locked.

Desired path:

```text
\\wsl.localhost\Ubuntu\home\beekeeper24\projects\DealMoa
```

Current active path during this handoff:

```text
\\wsl.localhost\Ubuntu\home\beekeeper24\projects\새 폴더
```

## Decisions Made

- Project name: `딜모아` / `DealMoa`.
- Main portfolio axis: search/recommendation backend, not ordinary shopping CRUD.
- Stack: Next.js/React frontend, FastAPI backend, PostgreSQL, Elasticsearch + Nori, Kafka, Celery/Redis, Prometheus/Grafana, JMeter.
- General search: BM25/Nori/exact/ngram/synonym/fuzzy fallback. No vector by default.
- AI search: search-bar AI button, structured intent, vector search, explanation.
- Hot-deal ranking: price first, interest second.
- Auction home ranking: actual auction activity first.
- Reports require admin judgment before affecting visibility/ranking.
- User submissions and verified reviews require AI first-pass review plus admin approval.

## Next Activation Steps

1. Rename the folder to `DealMoa` after the active session releases the directory lock.
2. Initialize git if needed.
3. Create the initial repo structure.
4. Scaffold Docker Compose profiles:
   - `core`
   - `worker`
   - `event`
   - `observability`
5. Implement Milestone 1:
   - Next.js shell
   - FastAPI shell
   - PostgreSQL
   - Elasticsearch with Nori
   - Redis
   - basic health checks
6. Keep Notion updated under `작업일지 > DealMoa`.
