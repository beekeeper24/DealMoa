# JMeter Local Baseline Observation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the current JMeter baseline against the local Korean demo dataset and document the first observed summary values.

**Architecture:** Do not commit raw JMeter result files. Use the existing Docker Compose `core` and `loadtest` profiles, existing Korean demo seed/reindex CLI, and existing `infra/jmeter/summarize_jtl.py` summary tool.

**Tech Stack:** Docker Compose, FastAPI, PostgreSQL, Elasticsearch, JMeter, Python `uv`.

---

## File Structure

- Modify `docs/performance.md`
  - Add a local baseline observation section with date, environment, command sequence, summary output, interpretation, and caveats.
- Modify `docs/handoff.md`
  - Add a completed-scope note for the local baseline observation.
- Modify `infra/jmeter/dealmoa-search-baseline.jmx`
  - Fix the response assertion so HTTP `200` API responses are counted as successful samples.
- Modify `infra/jmeter/README.md`
  - Document the explicit HTTP `200` assertion expectation.
- Keep generated files under `infra/jmeter/results/` untracked.

## Tasks

### Task 1: Prepare Local Runtime

**Files:**
- Read: `docker-compose.yml`
- Read: `infra/jmeter/README.md`

- [x] **Step 1: Confirm Docker Compose profiles and service names**

Run:

```bash
docker compose config --services
```

Expected: API, PostgreSQL, Elasticsearch, and JMeter-related services are present.

- [x] **Step 2: Start core services**

Run:

```bash
docker compose --profile core up -d
```

Expected: required services are created or already running.

### Task 2: Seed Search Data

**Files:**
- Runtime only.

- [x] **Step 1: Run Korean demo seed with reindex**

Run:

```bash
docker compose --profile core exec api uv run python -m app.modules.demo_seed.cli --reindex
```

Expected: command exits with code 0 and search indexes are rebuilt.

### Task 3: Run JMeter And Summarize Results

**Files:**
- Generated, untracked: `infra/jmeter/results/dealmoa-search-baseline.jtl`
- Generated, untracked: `infra/jmeter/results/jmeter.log`

- [x] **Step 1: Run the baseline**

Run:

```bash
docker compose --profile core --profile loadtest run --rm jmeter
```

Expected: command exits with code 0 and writes the `.jtl` result file.

- [x] **Step 2: Summarize as text**

Run:

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl
```

Expected: output includes overall and per-label metrics.

- [x] **Step 3: Summarize as JSON**

Run:

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl --json
```

Expected: output is parseable JSON.

### Task 4: Document Observation And Verify

**Files:**
- Modify `docs/performance.md`
- Modify `docs/handoff.md`

- [x] **Step 1: Add observation section**

Document:

- Date: `2026-06-05`
- Environment: local WSL Docker Compose, Korean demo seed, reindex before run
- JMeter settings used by default env values
- Summary output
- Caveat: local demo observation, not production SLO, not a threshold gate

- [x] **Step 2: Verify generated files remain untracked**

Run:

```bash
git status --short
```

Expected: generated `infra/jmeter/results/*.jtl` and `jmeter.log` are ignored.

- [x] **Step 3: Run documentation and backend checks**

Run:

```bash
uv run ruff check apps/api apps/consumer apps/worker infra/jmeter
MYPYPATH=apps/api:apps/consumer:apps/worker uv run mypy apps/api/app apps/api/tests apps/consumer/consumer_app apps/consumer/tests apps/worker/worker_app apps/worker/tests infra/jmeter/summarize_jtl.py infra/jmeter/tests
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests infra/jmeter/tests -q
git diff --check
```

Expected: all checks pass.

## Self-Review

- Spec coverage: Issue #88 asks for one local baseline observation using the existing JMeter and summary tooling. Tasks 1-4 cover runtime preparation, seeding, execution, summary, documentation, and verification.
- Placeholder scan: No TBD/TODO/fill-in wording.
- Type consistency: This slice does not add new code APIs.
