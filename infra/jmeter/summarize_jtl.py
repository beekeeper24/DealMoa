from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = frozenset({"elapsed", "label", "success"})


@dataclass(frozen=True)
class Sample:
    label: str
    elapsed_ms: int
    success: bool


@dataclass(frozen=True)
class MetricSummary:
    count: int
    success_count: int
    failure_count: int
    error_rate: float
    avg_ms: float
    p95_ms: int
    max_ms: int


@dataclass(frozen=True)
class Summary:
    overall: MetricSummary
    labels: dict[str, MetricSummary]


def parse_jtl(path: Path) -> list[Sample]:
    with path.open(newline="", encoding="utf-8") as result_file:
        reader = csv.DictReader(result_file)
        _validate_columns(path, reader.fieldnames)

        samples: list[Sample] = []
        for line_number, row in enumerate(reader, start=2):
            samples.append(_parse_row(path, line_number, row))

    return samples


def summarize_samples(samples: Sequence[Sample]) -> Summary:
    label_groups: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        label_groups[sample.label].append(sample)

    return Summary(
        overall=_summarize_group(samples),
        labels={
            label: _summarize_group(label_samples)
            for label, label_samples in sorted(label_groups.items())
        },
    )


def render_text(summary: Summary) -> str:
    lines = [
        "JMeter Summary",
        f"overall: {_format_metric(summary.overall)}",
    ]

    if summary.labels:
        lines.append("by label:")
        for label, metric in summary.labels.items():
            lines.append(f"- {label}: {_format_metric(metric)}")
    else:
        lines.append("by label: no samples")

    return "\n".join(lines)


def render_json(summary: Summary) -> str:
    payload = {
        "overall": _metric_to_payload(summary.overall),
        "labels": {
            label: _metric_to_payload(metric) for label, metric in summary.labels.items()
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize a JMeter CSV .jtl result file.",
    )
    parser.add_argument("result_file", type=Path, help="Path to a JMeter CSV .jtl file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    args = parser.parse_args(argv)

    try:
        summary = summarize_samples(parse_jtl(args.result_file))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output = render_json(summary) if args.json else render_text(summary)
    print(output)
    return 0


def _validate_columns(path: Path, fieldnames: Sequence[str] | None) -> None:
    columns = set(fieldnames or [])
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{path} is missing required columns: {joined}")


def _parse_row(path: Path, line_number: int, row: dict[str, str | None]) -> Sample:
    elapsed_raw = row["elapsed"]
    label_raw = row["label"]
    success_raw = row["success"]

    if elapsed_raw is None or elapsed_raw.strip() == "":
        raise ValueError(f"{path}:{line_number} has empty elapsed value")
    if label_raw is None or label_raw.strip() == "":
        raise ValueError(f"{path}:{line_number} has empty label value")
    if success_raw is None or success_raw.strip() == "":
        raise ValueError(f"{path}:{line_number} has empty success value")

    try:
        elapsed_ms = int(elapsed_raw)
    except ValueError as exc:
        raise ValueError(
            f"{path}:{line_number} has invalid elapsed value: {elapsed_raw!r}",
        ) from exc

    if elapsed_ms < 0:
        raise ValueError(f"{path}:{line_number} has negative elapsed value: {elapsed_ms}")

    success = _parse_success(path, line_number, success_raw)
    return Sample(label=label_raw.strip(), elapsed_ms=elapsed_ms, success=success)


def _parse_success(path: Path, line_number: int, raw_value: str) -> bool:
    normalized = raw_value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"{path}:{line_number} has invalid success value: {raw_value!r}")


def _summarize_group(samples: Sequence[Sample]) -> MetricSummary:
    count = len(samples)
    if count == 0:
        return MetricSummary(
            count=0,
            success_count=0,
            failure_count=0,
            error_rate=0.0,
            avg_ms=0.0,
            p95_ms=0,
            max_ms=0,
        )

    latencies = sorted(sample.elapsed_ms for sample in samples)
    success_count = sum(1 for sample in samples if sample.success)
    failure_count = count - success_count
    p95_index = math.ceil(0.95 * count) - 1

    return MetricSummary(
        count=count,
        success_count=success_count,
        failure_count=failure_count,
        error_rate=failure_count / count,
        avg_ms=sum(latencies) / count,
        p95_ms=latencies[p95_index],
        max_ms=latencies[-1],
    )


def _format_metric(metric: MetricSummary) -> str:
    return (
        f"count={metric.count} "
        f"success={metric.success_count} "
        f"failure={metric.failure_count} "
        f"error_rate={metric.error_rate:.2%} "
        f"avg={metric.avg_ms:.1f}ms "
        f"p95={metric.p95_ms}ms "
        f"max={metric.max_ms}ms"
    )


def _metric_to_payload(metric: MetricSummary) -> dict[str, Any]:
    return {
        "count": metric.count,
        "successCount": metric.success_count,
        "failureCount": metric.failure_count,
        "errorRate": metric.error_rate,
        "avgMs": metric.avg_ms,
        "p95Ms": metric.p95_ms,
        "maxMs": metric.max_ms,
    }


if __name__ == "__main__":
    raise SystemExit(main())
