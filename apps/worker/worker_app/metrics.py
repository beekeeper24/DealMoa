from time import monotonic
from typing import Any

from celery import signals  # type: ignore[import-untyped]
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    start_http_server,
)


class WorkerMetrics:
    def __init__(self, *, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.tasks_total = Counter(
            "dealmoa_worker_tasks_total",
            "Total Celery tasks completed by DealMoa workers.",
            ["status", "task"],
            registry=self.registry,
        )
        self.task_duration_seconds = Histogram(
            "dealmoa_worker_task_duration_seconds",
            "Celery task duration in seconds for DealMoa workers.",
            ["task"],
            registry=self.registry,
        )

    def record_task_result(self, *, task_name: str, status: str, duration_seconds: float) -> None:
        self.tasks_total.labels(status=status, task=task_name).inc()
        self.task_duration_seconds.labels(task=task_name).observe(duration_seconds)

    def generate(self) -> bytes:
        return generate_latest(self.registry)


worker_metrics = WorkerMetrics()
_metrics_server_started = False
_metrics_enabled = True
_metrics_port = 9102
_signals_configured = False
_task_start_times: dict[str, float] = {}


def generate_worker_metrics() -> bytes:
    return worker_metrics.generate()


def start_worker_metrics_server(*, enabled: bool, port: int) -> None:
    global _metrics_server_started
    if not enabled or _metrics_server_started:
        return
    start_http_server(port, registry=worker_metrics.registry)
    _metrics_server_started = True


def configure_worker_metrics(*, enabled: bool, port: int) -> None:
    global _metrics_enabled, _metrics_port, _signals_configured
    _metrics_enabled = enabled
    _metrics_port = port
    if _signals_configured:
        return
    signals.worker_ready.connect(_on_worker_ready, weak=False)
    signals.task_prerun.connect(_on_task_prerun, weak=False)
    signals.task_success.connect(_on_task_success, weak=False)
    signals.task_failure.connect(_on_task_failure, weak=False)
    _signals_configured = True


def _on_worker_ready(**_: Any) -> None:
    start_worker_metrics_server(enabled=_metrics_enabled, port=_metrics_port)


def _on_task_prerun(task_id: str | None = None, **_: Any) -> None:
    if task_id is not None:
        _task_start_times[task_id] = monotonic()


def _on_task_success(sender: Any = None, **kwargs: Any) -> None:
    task_name = _task_name(sender)
    task_id = _task_id(sender=sender, kwargs=kwargs)
    _record_task_signal(task_name=task_name, task_id=task_id, status="succeeded")


def _on_task_failure(sender: Any = None, task_id: str | None = None, **kwargs: Any) -> None:
    task_name = _task_name(sender)
    signal_task_id = task_id or _task_id(sender=sender, kwargs=kwargs)
    _record_task_signal(task_name=task_name, task_id=signal_task_id, status="failed")


def _record_task_signal(*, task_name: str, task_id: str | None, status: str) -> None:
    duration_seconds = 0.0
    if task_id is not None:
        started_at = _task_start_times.pop(task_id, None)
        if started_at is not None:
            duration_seconds = max(monotonic() - started_at, 0.0)
    worker_metrics.record_task_result(
        task_name=task_name,
        status=status,
        duration_seconds=duration_seconds,
    )


def _task_name(sender: Any) -> str:
    name = getattr(sender, "name", None)
    return name if isinstance(name, str) else "unknown"


def _task_id(*, sender: Any, kwargs: dict[str, Any]) -> str | None:
    task_id = kwargs.get("task_id")
    if isinstance(task_id, str):
        return task_id
    request = getattr(sender, "request", None)
    request_id = getattr(request, "id", None)
    return request_id if isinstance(request_id, str) else None
