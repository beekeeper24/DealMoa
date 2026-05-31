# Crawler Ingestion Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for event/job processing, idempotency, and external URL boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder mock crawler task with a safe ingestion foundation that turns deterministic crawled offer items into pending submissions for admin review.

**Architecture:** Keep the worker job as a producer of `Submission` rows only. It reuses the submission intake validation and mock AI first-pass review. It does not publish Product/Deal/Auction rows and does not fetch real external pages in this slice.

**Tech Stack:** Celery worker, SQLAlchemy, Pydantic submission schemas, existing FastAPI domain modules.

---

## Scope

- Add a deterministic mock crawl item source.
- Add worker ingestion logic that creates pending submissions through `SubmissionsUseCases`.
- Create/reuse a system crawler user for worker-created submissions.
- Preserve source URL idempotency: duplicate crawl items return existing submissions.
- Return a stable task summary with scanned, created, and duplicate counts.
- Document crawler ingestion boundaries.

## Non-goals

- No live crawling or HTTP fetching.
- No source allowlist/blocklist beyond existing `http/https` validation.
- No automatic publishing.
- No product auto-matching during ingestion.
- No scheduler changes beyond the existing registered task.
- No UI changes.

## Security Boundaries

- Crawled URLs are stored and reviewed; they are not fetched by this task.
- Ingestion creates `pending_review` submissions only.
- Admin approval remains the only publishing path.
- Duplicate source URLs do not create extra queue rows.
- The system crawler user is non-admin.

## Verification

- Worker tests for task registration and stable summary payload.
- Worker integration test with SQLite database: first run creates submissions, second run reports duplicates.
- API submission tests continue to pass.
- Focused cso review for external URL and async job boundaries.

## Implementation Checklist

- [x] Add crawler ingestion plan.
- [x] Add worker tests for mock crawl ingestion and idempotency.
- [x] Implement system crawler user and submission ingestion.
- [x] Update docs and run focused security review.
