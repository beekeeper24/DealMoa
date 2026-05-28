from worker_app.celery_app import celery_app
from worker_app.tasks import (
    ai_review_submission_mock,
    crawl_hot_deals_mock,
    rebuild_search_index,
)


def test_initial_celery_tasks_are_registered() -> None:
    assert "dealmoa.crawl_hot_deals_mock" in celery_app.tasks
    assert "dealmoa.ai_review_submission_mock" in celery_app.tasks
    assert "dealmoa.rebuild_search_index" in celery_app.tasks


def test_mock_tasks_return_stable_summary_payloads() -> None:
    assert crawl_hot_deals_mock() == {"task": "crawl_hot_deals_mock", "created": 0}
    assert ai_review_submission_mock("submission-1") == {
        "task": "ai_review_submission_mock",
        "submissionId": "submission-1",
        "decision": "needs_admin_review",
    }
    assert rebuild_search_index() == {
        "task": "rebuild_search_index",
        "products": 0,
        "deals": 0,
        "auctions": 0,
    }
