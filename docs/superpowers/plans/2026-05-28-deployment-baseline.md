# Deployment Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix DealMoa's deployment contract around Vercel for web and Railway for API/services while keeping local development as a compatible profile.

**Architecture:** Vercel owns the Next.js web runtime from `apps/web`; Railway owns the FastAPI API runtime from the repo root using `apps/api/Dockerfile`. Runtime differences must be environment values, not code branches. Docker Compose remains local infrastructure and demo tooling, not the production deployment target.

**Tech Stack:** Vercel, Railway, Next.js, FastAPI, Docker, Docker Compose, GitHub Actions.

---

## Tasks

### Task 1: Document The Deployment Contract

- [x] Add `docs/deployment.md` with Vercel/Railway service ownership, environment variables, OAuth callback URLs, CORS/cookie rules, migration policy, and local parity notes.
- [x] Update `docs/planning.md`, `docs/architecture.md`, and `docs/handoff.md` so future work sees Vercel/Railway as fixed project decisions.

### Task 2: Align Env Names

- [x] Update `.env.example` so production-facing names use `NEXT_PUBLIC_API_BASE_URL`, `PORT`, and the same API env variables Railway will receive.
- [x] Keep local compatibility for existing `WEB_PUBLIC_API_BASE_URL` through Docker Compose fallback only.

### Task 3: Make API Container Railway-Friendly

- [x] Update `apps/api/Dockerfile` to listen on `${PORT:-8000}`.
- [x] Pass `PORT` through Docker Compose while preserving local `API_PORT` host mapping.
- [x] Add CI coverage for the API Docker image build.

### Task 4: Verify

- [x] Run API config tests and lint/typecheck.
- [x] Run web lint/typecheck/build.
- [x] Run Docker Compose config validation.
- [x] Run focused deployment/security grep for hard-coded localhost/prod secrets in runtime code.
