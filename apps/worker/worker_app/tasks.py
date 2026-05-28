from worker_app.celery_app import celery_app


@celery_app.task(name="dealmoa.crawl_hot_deals_mock")  # type: ignore[untyped-decorator]
def crawl_hot_deals_mock() -> dict[str, object]:
    return {"task": "crawl_hot_deals_mock", "created": 0}


@celery_app.task(name="dealmoa.ai_review_submission_mock")  # type: ignore[untyped-decorator]
def ai_review_submission_mock(submission_id: str) -> dict[str, object]:
    return {
        "task": "ai_review_submission_mock",
        "submissionId": submission_id,
        "decision": "needs_admin_review",
    }


@celery_app.task(name="dealmoa.rebuild_search_index")  # type: ignore[untyped-decorator]
def rebuild_search_index() -> dict[str, object]:
    return {
        "task": "rebuild_search_index",
        "products": 0,
        "deals": 0,
        "auctions": 0,
    }
