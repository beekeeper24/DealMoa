# JMeter Load-Test Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable local JMeter baseline for DealMoa search/ranking APIs so performance checks can start from a documented, repeatable scenario.

**Architecture:** Keep load-test assets under `infra/jmeter` and make Docker Compose own only the local runner profile. The JMeter plan uses variables for API base URL, thread count, ramp-up, duration, and query so the same file can run against local Docker, local API, or a later deployed Railway API.

**Tech Stack:** Apache JMeter JMX, Docker Compose, shell script, XML validation, docs.

---

### Task 1: Add JMeter Scenario Assets

**Files:**
- Create: `infra/jmeter/dealmoa-search-baseline.jmx`
- Create: `infra/jmeter/README.md`

- [x] Add a JMX test plan with user-defined variables.
- [x] Include health, product search, hot-deal ranking, and auction activity ranking HTTP samplers.
- [x] Add response assertions for HTTP 2xx/3xx success.
- [x] Add a README explaining local and deployed API usage.

### Task 2: Add Local Runner Wiring

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [x] Add `loadtest` profile service using a JMeter container.
- [x] Mount the JMeter plan and write results into `infra/jmeter/results`.
- [x] Add `JMETER_API_BASE_URL`, `JMETER_THREADS`, `JMETER_RAMP_SECONDS`, `JMETER_DURATION_SECONDS`, and `JMETER_SEARCH_QUERY` examples.

### Task 3: Update Project Docs

**Files:**
- Modify: `docs/performance.md`
- Modify: `docs/handoff.md`

- [x] Document the baseline scenario, variables, commands, and result files.
- [x] Record that this is a repeatable baseline, not a tuned SLO or production load test.

### Task 4: Verification And Integration

**Files:**
- Modify this plan checklist as steps complete.

- [x] Validate JMX XML structure.
- [x] Validate Docker Compose config with `.env.example`.
- [x] Run lint/type/test smoke checks that should remain unaffected.
- [x] Run `git diff --check`.
- [ ] Commit, push, open PR to `develop`, wait for checks, merge, sync local `develop`, and create a Notion work log.

## Acceptance Criteria

- Developers can run a local JMeter baseline through Docker Compose.
- The test plan has no secrets or hard-coded local-only API URL.
- The scenario exercises health, search, hot-deal ranking, and auction activity ranking endpoints.
- Documentation explains how to read the generated `.jtl` result file at a basic level.
