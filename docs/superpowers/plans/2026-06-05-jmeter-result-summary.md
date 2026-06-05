# JMeter Result Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small JMeter `.jtl` CSV summary tool so local load-test runs can be read consistently without opening raw result files.

**Architecture:** Keep the tool under `infra/jmeter` next to the JMeter plan. Use only Python standard library code so it works in the existing root `uv` dev environment and CI without adding runtime dependencies.

**Tech Stack:** Python 3.12, `argparse`, `csv`, `json`, `pytest`, `ruff`, `mypy`.

---

## File Structure

- Create `infra/jmeter/summarize_jtl.py`
  - Parse JMeter CSV `.jtl` files.
  - Compute overall and per-label request count, success count, failure count, error rate, average latency, p95 latency, and max latency.
  - Render text output by default and JSON output with `--json`.
- Create `infra/__init__.py` and `infra/jmeter/__init__.py`
  - Let tests and mypy import the JMeter summary module through a stable package path.
- Create `infra/jmeter/tests/conftest.py`
  - Add the repository root to the pytest import path for local JMeter tests.
- Create `infra/jmeter/tests/fixtures/search-baseline-sample.jtl`
  - Small stable sample file for tests and CLI examples.
- Create `infra/jmeter/tests/test_summarize_jtl.py`
  - Focused tests for parsing, summary math, empty result handling, missing column validation, and JSON CLI output.
- Modify `.github/workflows/ci.yml`
  - Include `infra/jmeter` in backend lint/type/test checks.
- Modify `infra/jmeter/README.md`
  - Document how to run the summary command after JMeter.
- Modify `docs/performance.md`
  - Document how to read JMeter output and clarify that threshold gates remain deferred.
- Modify `docs/handoff.md`
  - Add a completed-scope note after the slice is verified.

## Tasks

### Task 1: Add Summary Tests And Fixture

**Files:**
- Create: `infra/jmeter/tests/fixtures/search-baseline-sample.jtl`
- Create: `infra/jmeter/tests/test_summarize_jtl.py`

- [x] **Step 1: Add a sample JMeter CSV fixture**

```csv
timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect
1760000000000,40,GET /health,200,OK,Thread Group 1-1,text,true,,128,64,1,1,http://api:8000/health,35,0,4
1760000000100,120,GET /api/v1/search/products,200,OK,Thread Group 1-1,text,true,,1024,128,1,1,http://api:8000/api/v1/search/products?q=갤럭시,105,0,9
1760000000200,300,GET /api/v1/search/products,500,Error,Thread Group 1-2,text,false,server error,512,128,2,2,http://api:8000/api/v1/search/products?q=갤럭시,280,0,12
1760000000300,90,GET /api/v1/search/deals/hot,200,OK,Thread Group 1-1,text,true,,900,128,2,2,http://api:8000/api/v1/search/deals/hot,82,0,5
```

- [x] **Step 2: Add tests for parser, summary, and CLI JSON**

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from summarize_jtl import parse_jtl, render_json, summarize_samples


FIXTURE = Path(__file__).parent / "fixtures" / "search-baseline-sample.jtl"


def test_summarize_samples_groups_overall_and_by_label() -> None:
    samples = parse_jtl(FIXTURE)

    summary = summarize_samples(samples)

    assert summary.overall.count == 4
    assert summary.overall.success_count == 3
    assert summary.overall.failure_count == 1
    assert summary.overall.error_rate == 0.25
    assert summary.overall.avg_ms == 137.5
    assert summary.overall.p95_ms == 300
    assert summary.overall.max_ms == 300
    assert summary.labels["GET /api/v1/search/products"].count == 2
    assert summary.labels["GET /api/v1/search/products"].failure_count == 1


def test_header_only_jtl_returns_empty_summary(tmp_path: Path) -> None:
    result_file = tmp_path / "empty.jtl"
    result_file.write_text("elapsed,label,success\n", encoding="utf-8")

    summary = summarize_samples(parse_jtl(result_file))

    assert summary.overall.count == 0
    assert summary.labels == {}


def test_missing_required_columns_raise_clear_error(tmp_path: Path) -> None:
    result_file = tmp_path / "broken.jtl"
    result_file.write_text("elapsed,label\n10,GET /health\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns: success"):
        parse_jtl(result_file)


def test_cli_json_output_is_machine_readable() -> None:
    completed = subprocess.run(
        [sys.executable, "infra/jmeter/summarize_jtl.py", str(FIXTURE), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["overall"]["count"] == 4
    assert payload["labels"]["GET /health"]["successCount"] == 1
```

- [x] **Step 3: Run tests to verify they fail before implementation**

Run:

```bash
uv run pytest infra/jmeter/tests -q
```

Expected: fail because `summarize_jtl.py` does not exist yet.

### Task 2: Implement The Summary Tool

**Files:**
- Create: `infra/jmeter/summarize_jtl.py`

- [x] **Step 1: Implement the parser, summary model, renderers, and CLI**

Use these public functions:

```python
parse_jtl(path: Path) -> list[Sample]
summarize_samples(samples: Sequence[Sample]) -> Summary
render_text(summary: Summary) -> str
render_json(summary: Summary) -> str
main(argv: Sequence[str] | None = None) -> int
```

Required behavior:

- Require CSV columns `elapsed`, `label`, and `success`.
- Parse `elapsed` as integer milliseconds.
- Accept `success` values `true` and `false`, case-insensitively.
- Compute p95 with nearest-rank percentile: `ceil(0.95 * count) - 1`.
- Print text output by default.
- Print compact, stable JSON with `--json`.

- [x] **Step 2: Run focused tests**

Run:

```bash
uv run pytest infra/jmeter/tests -q
```

Expected: all tests pass.

### Task 3: Wire CI And Docs

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `infra/jmeter/README.md`
- Modify: `docs/performance.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Include the JMeter tool in CI**

Update backend CI commands:

```yaml
- name: Lint backend services
  run: uv run ruff check apps/api apps/consumer apps/worker infra/jmeter

- name: Typecheck backend services
  run: MYPYPATH=apps/api:apps/consumer:apps/worker uv run mypy apps/api/app apps/api/tests apps/consumer/consumer_app apps/consumer/tests apps/worker/worker_app apps/worker/tests infra/jmeter/summarize_jtl.py infra/jmeter/tests

- name: Test backend services
  run: PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests infra/jmeter/tests
```

- [x] **Step 2: Document local usage**

Add these commands to `infra/jmeter/README.md` and `docs/performance.md`:

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/results/dealmoa-search-baseline.jtl --json
```

- [x] **Step 3: Update handoff**

Add the completed scope:

- `infra/jmeter/summarize_jtl.py` reads JMeter CSV `.jtl` results.
- Output includes overall and per-label counts, success/failure counts, error rate, average latency, p95 latency, and max latency.
- CI covers the summary tool with lint, mypy, and pytest.
- Performance threshold gates remain deferred.

### Task 4: Verify And Integrate

**Files:**
- Verify all changed files.

- [x] **Step 1: Run focused JMeter tests**

```bash
uv run pytest infra/jmeter/tests -q
```

- [x] **Step 2: Run backend lint**

```bash
uv run ruff check apps/api apps/consumer apps/worker infra/jmeter
```

- [x] **Step 3: Run backend typecheck**

```bash
MYPYPATH=apps/api:apps/consumer:apps/worker uv run mypy apps/api/app apps/api/tests apps/consumer/consumer_app apps/consumer/tests apps/worker/worker_app apps/worker/tests infra/jmeter/summarize_jtl.py infra/jmeter/tests
```

- [x] **Step 4: Run backend tests**

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests infra/jmeter/tests
```

- [x] **Step 5: Run CLI smoke check**

```bash
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/tests/fixtures/search-baseline-sample.jtl
uv run python infra/jmeter/summarize_jtl.py infra/jmeter/tests/fixtures/search-baseline-sample.jtl --json
```

- [x] **Step 6: Check patch hygiene**

```bash
git diff --check
git status --short
```

## Self-Review

- Spec coverage: Issue #86 asks for JMeter CSV parsing, overall/per-label metrics, text/JSON output, sample tests, CI coverage, and docs. Tasks 1-4 cover each item.
- Placeholder scan: No task uses TBD/TODO/fill-in wording.
- Type consistency: The planned functions use `Sample`, `Summary`, and `MetricSummary` consistently across tests and implementation.
