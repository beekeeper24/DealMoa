from typing import Literal, Protocol

from celery import Celery  # type: ignore[import-untyped]

CrawlerTaskName = Literal["crawl_hot_deals_mock", "crawl_live_urls"]
CELERY_CRAWLER_TASK_NAMES: dict[CrawlerTaskName, str] = {
    "crawl_hot_deals_mock": "dealmoa.crawl_hot_deals_mock",
    "crawl_live_urls": "dealmoa.crawl_live_urls",
}


class CrawlerTaskQueue(Protocol):
    def enqueue(self, task_name: CrawlerTaskName) -> str: ...


class CeleryCrawlerTaskQueue:
    def __init__(self, *, broker_url: str) -> None:
        self._celery_app = Celery("dealmoa-api", broker=broker_url)

    def enqueue(self, task_name: CrawlerTaskName) -> str:
        result = self._celery_app.send_task(CELERY_CRAWLER_TASK_NAMES[task_name])
        return str(result.id)
