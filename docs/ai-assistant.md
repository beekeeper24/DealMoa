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
- Perform first-pass review for user offer submissions and future suspicious purchase
  verification escalations. Normal verified purchase reviews auto-publish after
  lightweight validation in the MVP and do not spend AI tokens.

## Current MVP Contract

AI search and purchase checks use an assistant provider boundary configured by
`AI_ASSISTANT_PROVIDER`. The default remains deterministic `mock`, preserving local and
CI behavior. `AI_ASSISTANT_PROVIDER=openai` can call the OpenAI Responses API, but model
output is still constrained to validated response models before any search or purchase
check response is built.

First-pass submission/review checks use a separate provider boundary configured by
`AI_REVIEW_PROVIDER`.

Routes:

```http
POST /api/v1/ai/search
GET /api/v1/ai/products/{product_id}/purchase-check
```

`POST /ai/search` parses a lightweight `SearchIntent` from the user query and calls the
existing product/deal/auction search use cases. The provider can emit only allowlisted
target types and filters, such as `targetTypes`, `category`, and `maxPrice`. Raw model
output is never used as Elasticsearch DSL.

`GET /ai/products/{product_id}/purchase-check` reads trusted product evidence from
PostgreSQL:

- product metadata and specs;
- active deals and auctions;
- price-history snapshots;
- approved verified reviews only.

The current recommendation is a `buy` / `watch` / `avoid` result with confidence and
summary. In mock mode this is deterministic. In OpenAI mode the provider can generate the
recommendation, confidence, and summary, but the evidence list is still built by server
code from trusted PostgreSQL rows.

## AI Assistant Provider

Provider settings:

```env
AI_ASSISTANT_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_ASSISTANT_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=8
```

`AI_ASSISTANT_PROVIDER=mock` is the local and CI default. `AI_ASSISTANT_PROVIDER=openai`
uses the OpenAI Responses API with Structured Outputs.

For AI search, the model must return only:

```json
{
  "query": "original user query",
  "normalizedQuery": "normalized query",
  "targetTypes": ["products", "deals"],
  "filters": {
    "category": "smartphone",
    "maxPrice": 1000000
  }
}
```

The server validates that response as `SearchIntent`. Invalid JSON, invalid schema, API
errors, timeout, or missing API key fall back to the mock parser.

For purchase checks, the model must return only:

```json
{
  "recommendation": "watch",
  "confidence": 0.63,
  "summary": "short user-facing explanation"
}
```

The model receives product metadata, active deals/auctions, price history, and approved
verified review title/body/rating. It does not receive proof references, admin notes,
AI review reasoning, hidden reviews, rejected reviews, pending reviews, discussion text,
or private user identifiers.

## First-Pass Review Provider

Provider settings:

```env
AI_REVIEW_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_REVIEW_MODEL=gpt-4o-mini
OPENAI_ASSISTANT_MODEL=gpt-4o-mini
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
review evidence only. User offer submissions still start as `pending_review`, and only
an admin action can publish or reject them. Normal verified purchase reviews do not call
this provider in the MVP auto-publish path; future suspicious-review escalation can store
AI evidence without directly deciding publication.

Provider failures, invalid JSON, or schema validation failures fall back to
`needs_admin_review`. Verified-review `proofReference` remains internal metadata and is
not sent to the model in this slice. Receipt image upload and OCR remain deferred.

User-triggered first-pass review calls are bounded by
`AI_REVIEW_USER_WINDOW_LIMIT` per `AI_REVIEW_USER_WINDOW_HOURS`. Usage is recorded in
PostgreSQL through `ai_review_usage_events`, so the initial protection works across API
process restarts and multiple API instances. Normal verified-review auto-publish does not
consume this quota because it does not call AI. Set the limit to `0` only for local
debugging when quota protection must be disabled.

## Guardrails

- Do not auto-publish user submissions.
- Do not treat community sentiment as fact.
- Validate LLM output with Pydantic.
- Use Structured Outputs for provider JSON when the selected model supports it.
- Use allowlisted filters and fields when building Elasticsearch queries.
- Keep AI assistant provider failure non-fatal by falling back to the mock provider.
- Do not expose proof references, AI review reasoning, or admin resolution notes in public
  purchase-check evidence.
- Do not execute raw model output as Elasticsearch DSL. Convert model output into
  `SearchIntent` first, then build queries from allowlisted fields.
