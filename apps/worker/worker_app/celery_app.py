from celery import Celery  # type: ignore[import-untyped]

from worker_app.config import WorkerSettings
from worker_app.metrics import configure_worker_metrics

settings = WorkerSettings()

celery_app = Celery(
    "dealmoa-worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["worker_app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "generate-auction-ending-soon-notifications": {
            "task": "dealmoa.generate_auction_ending_soon_notifications",
            "schedule": settings.auction_ending_soon_schedule_seconds,
        },
    },
)

configure_worker_metrics(
    enabled=settings.worker_metrics_enabled,
    port=settings.worker_metrics_port,
)
