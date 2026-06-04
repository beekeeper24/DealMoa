# Worker/Consumer Metrics MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add minimal Prometheus metrics for DealMoa Kafka consumers and Celery workers so local observability covers background processing, not only API requests.

**Architecture:** Keep metrics inside each runtime package because worker and consumer are separate processes. Each package owns a tiny metrics module that records counters/histograms and starts a Prometheus HTTP server only when enabled by environment settings. Docker Compose and Prometheus then wire those ports for local development.

**Tech Stack:** Python 3.12, prometheus-client, aiokafka consumer boundary, Celery task signals, Docker Compose, Prometheus, pytest, ruff, mypy.

---

### Task 1: Consumer Metrics

**Files:**
- Create: `apps/consumer/consumer_app/metrics.py`
- Modify: `apps/consumer/consumer_app/config.py`
- Modify: `apps/consumer/consumer_app/kafka.py`
- Test: `apps/consumer/tests/test_consumer_metrics.py`
- Test: `apps/consumer/tests/test_kafka_subscriber.py`

- [x] Add failing tests that assert consumer metrics settings default to enabled port `9101`, valid JSON messages record `status="handled"`, invalid JSON messages record `status="skipped"`, and handler exceptions record `status="failed"`.
- [x] Implement a consumer metrics module with `start_consumer_metrics_server`, `record_consumer_event`, and `generate_consumer_metrics`.
- [x] Wire `DomainEventSubscriber` to accept `consumer_name` and an optional metrics recorder.
- [x] Keep existing subscriber behavior: invalid JSON is skipped, handler exceptions still propagate.

### Task 2: Worker Metrics

**Files:**
- Create: `apps/worker/worker_app/metrics.py`
- Modify: `apps/worker/worker_app/config.py`
- Modify: `apps/worker/worker_app/celery_app.py`
- Test: `apps/worker/tests/test_worker_metrics.py`
- Test: `apps/worker/tests/test_worker_config.py`

- [x] Add failing tests that assert worker metrics settings default to enabled port `9102`.
- [x] Add failing tests for success/failure task counters and duration histogram samples.
- [x] Implement worker metrics helpers plus Celery signal handlers for task prerun, success, and failure.
- [x] Start the worker metrics HTTP server on Celery worker readiness only when `WORKER_METRICS_ENABLED=true`.

### Task 3: Local Observability Wiring

**Files:**
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `infra/prometheus/prometheus.yml`
- Modify: `infra/grafana/dashboards/api-overview.json`
- Modify: `docs/observability.md`
- Modify: `docs/handoff.md`

- [x] Add `CONSUMER_METRICS_ENABLED`, `CONSUMER_METRICS_PORT`, `WORKER_METRICS_ENABLED`, and `WORKER_METRICS_PORT`.
- [x] Expose metrics ports from `consumer` and `worker` containers.
- [x] Add Prometheus scrape jobs for `consumer:9101` and `worker:9102`.
- [x] Extend the local Grafana dashboard with simple worker/consumer throughput panels.
- [x] Document local URLs, metric names, and deferred production concerns.

### Task 4: Verification And Integration

**Files:**
- Modify this plan checklist as steps complete.

- [x] Run focused consumer/worker metrics tests.
- [x] Run backend/consumer/worker test suite.
- [x] Run ruff and mypy for Python apps.
- [x] Run Docker Compose config checks with `.env.example`.
- [x] Run `git diff --check`.
- [ ] Commit in Korean, push the branch, open PR to `develop`, wait for checks, merge, sync local `develop`, and create a Notion work log.

## Acceptance Criteria

- `consumer` exposes Prometheus text metrics when `CONSUMER_METRICS_ENABLED=true`.
- `worker` exposes Prometheus text metrics when `WORKER_METRICS_ENABLED=true`.
- Prometheus local profile scrapes API, consumer, and worker targets.
- The implementation stays local-MVP sized and does not attempt production Celery multiprocess metrics, alerting, or Kafka lag exporters.
