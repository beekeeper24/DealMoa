from celery import Celery  # type: ignore[import-untyped]

from worker_app.config import WorkerSettings

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
)
