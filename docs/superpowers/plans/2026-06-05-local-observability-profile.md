# Local Observability Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local Docker Compose `observability` profile that runs Prometheus and Grafana against the API `/metrics` endpoint.

**Architecture:** Keep observability infra under `infra/prometheus` and `infra/grafana`. Prometheus scrapes the API container on `api:8000/metrics`; Grafana provisions Prometheus as a datasource and ships a minimal API overview dashboard. This is local/dev scaffolding only, not production Railway/Vercel observability.

**Tech Stack:** Docker Compose, Prometheus, Grafana OSS provisioning, API `/metrics`.

---

### Task 1: Local Observability Infra

**Files:**
- Modify: `docker-compose.yml`
- Create: `infra/prometheus/prometheus.yml`
- Create: `infra/grafana/provisioning/datasources/prometheus.yml`
- Create: `infra/grafana/provisioning/dashboards/dashboards.yml`
- Create: `infra/grafana/dashboards/api-overview.json`
- Modify: `.env.example`

- [x] Add `prometheus` service under `observability` profile.
- [x] Add `grafana` service under `observability` profile.
- [x] Add persistent `prometheus_data` and `grafana_data` volumes.
- [x] Add Prometheus scrape config for `api:8000/metrics`.
- [x] Add Grafana datasource provisioning for Prometheus.
- [x] Add minimal API overview dashboard panels for request rate, error rate, and p95 latency.
- [x] Add port/admin env examples.

### Task 2: Docs And Verification

**Files:**
- Modify: `docs/observability.md`
- Modify: `docs/handoff.md`

- [x] Document local startup command and URLs.
- [x] Document current non-goals and production caveat.
- [x] Run `docker compose --profile observability config`.
- [x] Run `git diff --check`.
- [ ] Commit, push, open PR to `develop`, wait for CI, merge, sync `develop`, and create Notion work log.
