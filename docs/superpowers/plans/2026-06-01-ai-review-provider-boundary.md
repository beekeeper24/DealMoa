# AI Review Provider Boundary Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for AI prompt/output handling and publication safety. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hard-coded first-pass AI review functions with a provider boundary that can use mock or OpenAI review without allowing AI to publish content.

**Architecture:** Submission and verified-review use cases depend on an `AiReviewProvider` port. The default provider remains deterministic mock. The OpenAI adapter calls the Responses API with strict JSON schema output, then validates with Pydantic before returning a safe internal review result.

**Tech Stack:** FastAPI settings, Pydantic validation, `httpx`, existing submission/evidence use cases.

---

## Scope

- Add shared AI review result/input/provider abstractions.
- Add deterministic mock provider preserving current outputs.
- Add OpenAI provider adapter using Responses API structured output.
- Add safe fallback provider so provider errors never approve or auto-publish content.
- Wire submissions and verified reviews to the provider port.
- Add API settings and `.env.example`/Compose documentation for provider selection.
- Document OCR/upload remains deferred; verified review proof reference is not sent to the model in this slice.

## Non-goals

- No receipt image upload endpoint.
- No OCR engine integration.
- No automatic approve/reject publishing.
- No streaming or background async review migration.
- No AI search/purchase-check provider conversion.

## Security Boundaries

- AI output can set only `aiDecision` and `aiReason`; database status remains `pending_review`.
- OpenAI output is parsed as JSON and validated against an allowlisted decision enum.
- Provider failures fall back to `needs_admin_review`.
- Verified-review `proofReference` is treated as internal proof metadata and is not sent to the model.
- OpenAI API key is configured only through env and must never be committed.

## Verification

- Unit tests for OpenAI adapter request body, structured parsing, and safe fallback.
- Use-case tests showing provider results are stored while status remains `pending_review`.
- Existing submission/evidence API tests continue to pass.
- Focused CSO review for AI prompt/output, secrets, and publication boundary.

## Implementation Checklist

- [x] Add AI review provider plan.
- [x] Add provider and use-case tests.
- [x] Implement provider boundary and OpenAI adapter.
- [x] Wire API dependencies and environment docs.
- [x] Run focused security review and full verification.
