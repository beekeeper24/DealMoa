from prometheus_client import CollectorRegistry
from worker_app.metrics import WorkerMetrics


def test_worker_metrics_records_success_and_duration() -> None:
    metrics = WorkerMetrics(registry=CollectorRegistry())

    metrics.record_task_result(
        task_name="dealmoa.crawl_live_urls",
        status="succeeded",
        duration_seconds=1.25,
    )

    output = metrics.generate().decode("utf-8")
    assert (
        'dealmoa_worker_tasks_total{status="succeeded",task="dealmoa.crawl_live_urls"} 1.0'
        in output
    )
    assert (
        'dealmoa_worker_task_duration_seconds_count{task="dealmoa.crawl_live_urls"} 1.0'
        in output
    )
    assert (
        'dealmoa_worker_task_duration_seconds_sum{task="dealmoa.crawl_live_urls"} 1.25'
        in output
    )


def test_worker_metrics_records_failure() -> None:
    metrics = WorkerMetrics(registry=CollectorRegistry())

    metrics.record_task_result(
        task_name="dealmoa.crawl_live_urls",
        status="failed",
        duration_seconds=0.5,
    )

    assert (
        'dealmoa_worker_tasks_total{status="failed",task="dealmoa.crawl_live_urls"} 1.0'
        in metrics.generate().decode("utf-8")
    )
