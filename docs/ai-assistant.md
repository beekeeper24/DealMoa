# AI Assistant

## UX

- No floating chatbot.
- Use the same search input with a separate AI button.
- AI results are shown as a structured search result panel.
- Product/deal/auction detail pages can show an AI purchase-check button.

## Responsibilities

- Parse natural-language search into validated `SearchIntent`.
- Use Elasticsearch filters, BM25, vector search, and ranking signals.
- Explain recommendations using structured evidence.
- Generate purchase-check reports from price history, current deals/auctions, verified reviews, specs, and alternatives.
- Perform first-pass review for user submissions and purchase verification materials.
  Publication stays behind admin approval regardless of provider output.

## Current MVP Contract

AI search and purchase checks are still deterministic and do not call a real AI provider.
First-pass submission/review checks use a provider boundary configured by
`AI_REVIEW_PROVIDER`.

Routes:

```http
POST /api/v1/ai/search
GET /api/v1/ai/products/{product_id}/purchase-check
```

`POST /ai/search` parses a lightweight `SearchIntent` from the user query and calls the
existing product/deal/auction search use cases. The current parser only emits allowlisted
target types and filters, such as `targetTypes`, `category`, and `maxPrice`.

`GET /ai/products/{product_id}/purchase-check` reads trusted product evidence from
PostgreSQL:

- product metadata and specs;
- active deals and auctions;
- price-history snapshots;
- approved verified reviews only.

The current recommendation is a deterministic `buy` / `watch` / `avoid` result based on
current price, price history, and approved review presence. It is a stable contract for a
future LLM-backed explanation layer, not a final scoring model.

## First-Pass Review Provider

Provider settings:

```env
AI_REVIEW_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_REVIEW_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=8
AI_REVIEW_USER_WINDOW_LIMIT=20
AI_REVIEW_USER_WINDOW_HOURS=24
```

`AI_REVIEW_PROVIDER=mock` is the local and CI default. `AI_REVIEW_PROVIDER=openai`
uses the OpenAI Responses API with Structured Outputs. The model must return only:

```json
{
  "decision": "needs_admin_review",
  "reason": "short reviewer-facing reason"
}
```

Allowed decisions are `needs_admin_review` and `reject_candidate`. Both are stored as
review evidence only. Submissions and verified reviews still start as `pending_review`,
and only an admin action can publish or reject them.

Provider failures, invalid JSON, or schema validation failures fall back to
`needs_admin_review`. Verified-review `proofReference` remains internal metadata and is
not sent to the model in this slice. Receipt image upload and OCR remain deferred.

User-triggered submission and verified-review first-pass review calls are bounded by
`AI_REVIEW_USER_WINDOW_LIMIT` per `AI_REVIEW_USER_WINDOW_HOURS`. Usage is recorded in
PostgreSQL through `ai_review_usage_events`, so the initial protection works across API
process restarts and multiple API instances. Set the limit to `0` only for local
debugging when quota protection must be disabled.

## Guardrails

- Do not auto-publish user submissions.
- Do not treat community sentiment as fact.
- Validate LLM output with Pydantic.
- Use Structured Outputs for provider JSON when the selected model supports it.
- Use allowlisted filters and fields when building Elasticsearch queries.
- Do not expose proof references, AI review reasoning, or admin resolution notes in public
  purchase-check evidence.
- Do not execute raw model output as Elasticsearch DSL. Convert model output into
  `SearchIntent` first, then build queries from allowlisted fields.
