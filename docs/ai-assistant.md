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
- Perform first-pass review for user submissions and purchase verification materials. The
  MVP uses deterministic mock review results and keeps publication behind admin approval.

## Current MVP Contract

The first AI assistant foundation is deterministic and does not call a real AI provider.

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

## Guardrails

- Do not auto-publish user submissions.
- Do not treat community sentiment as fact.
- Validate LLM output with Pydantic.
- Use allowlisted filters and fields when building Elasticsearch queries.
- Do not expose proof references, AI review reasoning, or admin resolution notes in public
  purchase-check evidence.
- Do not execute raw model output as Elasticsearch DSL. Convert model output into
  `SearchIntent` first, then build queries from allowlisted fields.
