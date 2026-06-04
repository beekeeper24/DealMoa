# AI Assistant Provider Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mock-by-default, OpenAI-capable provider boundary for AI search intent parsing and purchase-check explanation.

**Architecture:** Keep current deterministic AI assistant behavior as the mock provider so local and CI stay stable. Add a provider port that returns validated `SearchIntent` and optional purchase-check recommendation text, then inject it into `AiAssistantUseCases`. OpenAI output is parsed through strict JSON schema and Pydantic before any search use case runs; raw model output is never executed as Elasticsearch DSL.

**Tech Stack:** FastAPI, Pydantic, httpx, pytest, existing OpenAI Responses API helper style.

---

### Task 1: RED Tests For Provider Contract

**Files:**
- Create: `apps/api/app/modules/ai_assistant/provider.py`
- Create: `apps/api/app/modules/ai_assistant/factory.py`
- Modify: `apps/api/tests/test_ai_assistant_api.py`
- Create: `apps/api/tests/test_ai_assistant_provider.py`
- Modify: `apps/api/tests/test_config.py`

- [x] Add a failing API/use-case test that injects a provider returning only `targetTypes=["products"]` and verifies only product search is called.
- [x] Add a failing provider test that OpenAI search intent calls `/responses` with strict JSON schema and returns a validated `SearchIntent`.
- [x] Add a failing provider test that invalid OpenAI output falls back to the mock intent instead of raising.
- [x] Add a failing provider test that purchase-check explanation output can override recommendation/confidence/summary while preserving server-built evidence.
- [x] Add a failing config test for `AI_ASSISTANT_PROVIDER`, `OPENAI_ASSISTANT_MODEL`, and shared OpenAI timeout/base URL settings.
- [x] Run focused tests and confirm they fail because the provider boundary/settings do not exist yet.

### Task 2: Provider And Use Case Implementation

**Files:**
- Create: `apps/api/app/modules/ai_assistant/provider.py`
- Create: `apps/api/app/modules/ai_assistant/factory.py`
- Modify: `apps/api/app/modules/ai_assistant/use_cases.py`
- Modify: `apps/api/app/modules/ai_assistant/router.py`
- Modify: `apps/api/app/core/config.py`
- Modify: `.env.example`

- [x] Implement `AiAssistantProvider` protocol with `parse_search_intent(query)` and `explain_purchase_check(...)`.
- [x] Move existing deterministic parsing/recommendation wording into `MockAiAssistantProvider`.
- [x] Implement `OpenAiAssistantProvider` using Responses API JSON schema and Pydantic validation.
- [x] Implement `SafeAiAssistantProvider` fallback to mock on provider failures.
- [x] Add `create_ai_assistant_provider(settings)`.
- [x] Inject provider into `AiAssistantUseCases` from the router factory.
- [x] Keep search execution based only on validated `SearchIntent.target_types`.
- [x] Keep purchase-check evidence built by server code only.
- [x] Run focused tests and confirm they pass.

### Task 3: Docs, Security Review, And PR

**Files:**
- Modify: `docs/ai-assistant.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/handoff.md`
- Modify: `docs/api-error-handling.md` only if new error codes are added.

- [x] Document provider settings, mock default, OpenAI mode, and fallback behavior.
- [x] Document that AI search output is validated `SearchIntent`, not raw Elasticsearch DSL.
- [x] Document that purchase-check prompt evidence excludes proof references, admin notes, hidden reviews, and discussion text.
- [x] Run focused security review for AI output handling and internal data exposure.
- [x] Run backend focused/full verification and web verification if response contracts changed.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync `develop`, and create Notion work log.
