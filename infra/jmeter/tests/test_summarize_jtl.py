import json
import subprocess
import sys
from pathlib import Path

import pytest

from infra.jmeter.summarize_jtl import parse_jtl, summarize_samples

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
