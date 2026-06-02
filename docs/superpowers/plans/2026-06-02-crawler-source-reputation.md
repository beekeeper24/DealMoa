# Crawler Source Reputation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for external URL and crawler ingestion boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first crawler source reputation and parser boundary before live crawling, so crawler-created submissions are accepted only from configured source profiles.

**Architecture:** Keep Celery ingestion as a submission producer only. Add a worker-side source policy and parser registry that validates source host, reputation, and offer parsing before calling `SubmissionsUseCases`.

**Tech Stack:** Celery worker, Pydantic settings, existing submissions use case.

---

## Scope

- Add crawler source profiles configured by environment.
- Add allowlisted mock source hosts with reputation labels.
- Add parser boundary that maps source items into `SubmissionCreateRequest`.
- Skip blocked or unknown sources before DB writes.
- Return stable task summary with scanned, accepted, created, duplicates, and skipped counts.
- Document source policy and deferred live HTTP fetching.

## Non-goals

- No live HTTP fetching.
- No robots.txt handling.
- No source-specific HTML parser.
- No source reputation scoring database.
- No automatic publishing.

## Security Boundaries

- Unknown source hosts are skipped.
- Blocked source profiles are skipped.
- Accepted crawler items still create only `pending_review` submissions.
- Crawler source URLs stay review-queue data until admin approval.
- The crawler system user remains non-admin.

## Verification

- Worker tests for allowlisted ingestion, idempotency, blocked source skip, and unknown host skip.
- Settings tests for source profile parsing.
- Focused CSO review for external URL/crawler boundaries.

## Implementation Checklist

- [x] Add crawler source reputation plan.
- [x] Add source policy/parser tests.
- [x] Implement source profiles and parser boundary.
- [x] Wire task summary and docs.
- [x] Run focused security review and full verification.
