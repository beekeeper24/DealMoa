from datetime import UTC, datetime

from app.db.base import Base
from app.modules.crawlers.models import CrawlerRunLog
from app.modules.crawlers.repository import CrawlerRunLogsRepository
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 6, 3, 1, 0, tzinfo=UTC)


def test_repository_creates_crawler_run_log_with_summary_counts() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        created = CrawlerRunLogsRepository(session).create(
            CrawlerRunLog(
                task_name="crawl_live_urls",
                status="succeeded",
                scanned_count=2,
                fetched_count=1,
                accepted_count=1,
                created_count=1,
                duplicate_count=0,
                skipped_count=1,
                skip_reasons_json={"host_rate_limited": 1},
                started_at=NOW,
                finished_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()

        persisted = session.scalar(select(CrawlerRunLog))
    finally:
        session.close()

    assert persisted is not None
    assert created.id == persisted.id
    assert persisted.task_name == "crawl_live_urls"
    assert persisted.status == "succeeded"
    assert persisted.scanned_count == 2
    assert persisted.fetched_count == 1
    assert persisted.skip_reasons_json == {"host_rate_limited": 1}
