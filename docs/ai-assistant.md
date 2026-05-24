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

## Guardrails

- Do not auto-publish user submissions.
- Do not treat community sentiment as fact.
- Validate LLM output with Pydantic.
- Use allowlisted filters and fields when building Elasticsearch queries.
