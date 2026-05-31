# AI Assistant Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for structured intent parsing, evidence selection, and API contract behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first AI search and purchase-check foundation without calling a real AI provider. The slice should fix API/UI contracts and prove that later OpenAI/Spring AI integration can plug into validated structured inputs and trusted evidence.

**Architecture:** Keep the first pass deterministic. `apps/api` adds an `ai_assistant` feature module that wraps existing search use cases plus product/evidence repositories. `apps/web` adds an AI search panel and product detail purchase-check action. No persistence or background jobs in this slice.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy repositories, existing Elasticsearch search use case boundary, Next.js, React, TypeScript.

---

## Scope

- Add `POST /api/v1/ai/search`.
- Parse a lightweight `SearchIntent` from a free-text query with allowlisted fields only.
- Use existing product/deal/auction search use cases to return grouped AI search candidates.
- Add simple deterministic explanations so the response shape is stable before real LLM integration.
- Add `GET /api/v1/ai/products/{product_id}/purchase-check`.
- Build purchase-check evidence from:
  - product metadata;
  - current active deals;
  - current active auctions;
  - price history snapshots;
  - approved public verified reviews.
- Add a deterministic recommendation: `buy`, `watch`, or `avoid`.
- Add web UI entry points:
  - search header AI button opens an AI result panel;
  - product detail can request and display a purchase-check report.

## Non-goals

- No real OpenAI/Spring AI provider call.
- No vector embeddings or vector index mapping.
- No streaming UI.
- No prompt persistence.
- No community discussion summarization.
- No user-specific personalization.

## API Contract

```http
POST /api/v1/ai/search
GET /api/v1/ai/products/{product_id}/purchase-check
```

`POST /ai/search` request:

```json
{
  "query": "갤럭시 100만원 이하 핫딜 찾아줘",
  "limit": 5
}
```

`GET /ai/products/{product_id}/purchase-check` returns a structured report with recommendation, confidence, summary, and evidence items.

## Security Boundaries

- User text is parsed into a validated intent object; it is not used as trusted code or raw query DSL.
- AI search uses allowlisted target types and filters only.
- Purchase check uses approved reviews only and must not expose proof references, AI review reasoning, or admin moderation notes.
- Later real LLM output must be parsed back into Pydantic schemas before use.

## Verification

- API tests for intent parsing, grouped AI search calls, purchase-check evidence selection, and not-found behavior.
- Web API/component tests for AI search panel and purchase-check report display.
- Focused lint/typecheck/tests before PR.

## Implementation Checklist

- [x] Add AI assistant backend schemas/use cases/router.
- [x] Add API tests for AI search and purchase check.
- [x] Add web typed client and UI states.
- [x] Add web tests for AI search and purchase check.
- [x] Update docs and run focused security review.
