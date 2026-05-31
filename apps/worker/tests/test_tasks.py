from worker_app.celery_app import celery_app
from worker_app.tasks import (
    ai_review_submission_mock,
    crawl_hot_deals_mock,
    generate_auction_ending_soon_notifications,
    rebuild_search_index,
)


def test_initial_celery_tasks_are_registered() -> None:
    assert "dealmoa.crawl_hot_deals_mock" in celery_app.tasks
    assert "dealmoa.ai_review_submission_mock" in celery_app.tasks
    assert "dealmoa.rebuild_search_index" in celery_app.tasks
    assert "dealmoa.generate_auction_ending_soon_notifications" in celery_app.tasks


def test_mock_tasks_return_stable_summary_payloads() -> None:
    assert crawl_hot_deals_mock() == {"task": "crawl_hot_deals_mock", "created": 0}
    assert ai_review_submission_mock("submission-1") == {
        "task": "ai_review_submission_mock",
        "submissionId": "submission-1",
        "decision": "needs_admin_review",
        "reason": "mock review passed: admin approval required",
    }
    assert rebuild_search_index() == {
        "task": "rebuild_search_index",
        "products": 0,
        "deals": 0,
        "auctions": 0,
    }


def test_auction_ending_soon_task_returns_stable_summary_for_empty_database(  # type: ignore[no-untyped-def]
    tmp_path,
    monkeypatch,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'dealmoa-worker-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AUCTION_ENDING_SOON_LOOKAHEAD_MINUTES", "60")
    monkeypatch.setenv("AUCTION_ENDING_SOON_BATCH_SIZE", "100")

    from app.db.base import Base
    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    assert generate_auction_ending_soon_notifications(
        now_iso="2026-05-29T10:00:00+00:00"
    ) == {
        "task": "generate_auction_ending_soon_notifications",
        "scannedAuctions": 0,
        "createdNotifications": 0,
    }
