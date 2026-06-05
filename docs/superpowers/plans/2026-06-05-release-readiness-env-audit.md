# Release Readiness Env Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document every environment variable, secret, OAuth setting, and deployment prerequisite needed before the first Vercel/Railway deployment.

**Architecture:** This is a documentation-only release-readiness slice. Use the existing settings classes, `.env.example`, deployment contract, and official Vercel/Railway docs as source evidence; do not create projects or enter secrets.

**Tech Stack:** Markdown docs, FastAPI/Pydantic settings, Next.js public env, Vercel, Railway.

---

## File Structure

- Create `docs/release-readiness.md`
  - User-facing deployment preparation checklist.
  - Separate Vercel web, Railway API, Railway worker, Railway consumer, OAuth provider, and optional AI provider requirements.
  - Mark what the user must prepare before deployment.
- Modify `docs/deployment.md`
  - Point to the release-readiness checklist and fill missing AI assistant / worker / consumer env details.
- Modify `docs/handoff.md`
  - Update next activation evidence with the new checklist.

## Tasks

### Task 1: Create Release Readiness Checklist

**Files:**
- Create: `docs/release-readiness.md`

- [x] **Step 1: Add deployment input checklist**

Include sections for:

- Domains needed.
- Vercel web env.
- Railway API env.
- Railway worker env.
- Railway consumer env.
- OAuth provider console setup.
- Optional OpenAI provider activation.
- Metrics exposure policy.

- [x] **Step 2: Clearly list what the user must prepare**

Required user-prepared values:

- Vercel web domain.
- Railway API domain.
- Railway PostgreSQL URL.
- Railway Redis URL.
- Elasticsearch URL reachable by Railway API/consumer.
- JWT secret with at least 32 random bytes.
- Google OAuth client id/secret.
- Kakao OAuth client id/secret.
- Naver OAuth client id/secret.
- Optional OpenAI API key if switching providers from `mock` to `openai`.

### Task 2: Update Deployment And Handoff Docs

**Files:**
- Modify: `docs/deployment.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Link deployment baseline to release readiness**

Add `docs/release-readiness.md` as the deployment preparation checklist.

- [x] **Step 2: Add missing env details**

Document:

- `AI_ASSISTANT_PROVIDER`
- `OPENAI_ASSISTANT_MODEL`
- worker service env
- consumer service env
- `API_METRICS_ENABLED=false` or protected metrics path for public API

- [x] **Step 3: Update handoff**

Next activation should remain full local demo smoke after this checklist is merged.

### Task 3: Security Review And Verification

**Files:**
- Verify changed docs.

- [x] **Step 1: Run focused security review**

Use gstack `cso` because this slice covers secrets, OAuth, cookie settings, and metrics exposure.

- [x] **Step 2: Check patch hygiene**

```bash
git diff --check
```

- [x] **Step 3: Inspect changed docs**

```bash
git diff --stat
git diff -- docs/release-readiness.md docs/deployment.md docs/handoff.md
```

- [ ] **Step 4: Commit and integrate**

Use a Korean commit message and PR into `develop`.

## Self-Review

- Spec coverage: Issue #92 asks for env, secrets, OAuth, metrics, and release-readiness documentation. Tasks 1-3 cover those outcomes.
- Placeholder scan: No TBD/TODO/fill-in wording.
- Type consistency: This slice changes docs only.
