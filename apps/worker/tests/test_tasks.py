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


def test_mock_crawler_task_ingests_pending_submissions_idempotently(  # type: ignore[no-untyped-def]
    tmp_path,
    monkeypatch,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'dealmoa-crawler-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("CRAWLER_SYSTEM_USER_ID", "crawler-user")
    monkeypatch.setenv("CRAWLER_SYSTEM_USER_EMAIL", "crawler@dealmoa.local")

    from app.db.base import Base
    from app.modules.auth.models import User
    from app.modules.submissions.models import Submission
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    first = crawl_hot_deals_mock(now_iso="2026-06-01T02:00:00+00:00")
    second = crawl_hot_deals_mock(now_iso="2026-06-01T02:05:00+00:00")

    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        submissions = list(session.scalars(select(Submission).order_by(Submission.source_url)))
        crawler_user = session.get(User, "crawler-user")
    finally:
        session.close()

    assert first == {
        "task": "crawl_hot_deals_mock",
        "scanned": 2,
        "created": 2,
        "duplicates": 0,
    }
    assert second == {
        "task": "crawl_hot_deals_mock",
        "scanned": 2,
        "created": 0,
        "duplicates": 2,
    }
    assert crawler_user is not None
    assert crawler_user.role == "USER"
    assert [submission.status for submission in submissions] == ["pending_review", "pending_review"]
    assert {submission.offer_type for submission in submissions} == {"auction", "deal"}
    assert {submission.user_id for submission in submissions} == {"crawler-user"}


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
