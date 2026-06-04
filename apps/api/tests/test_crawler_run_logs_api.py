from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.crawlers.models import CrawlerRunLog
from app.modules.crawlers.router import get_crawler_task_queue
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 6, 3, 1, 0, tzinfo=UTC)


class FakeAuthUseCases:
    def __init__(self, role: str = "ADMIN") -> None:
        self.role = role

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="admin-1",
            email="admin@example.com",
            nickname="Admin",
            role=self.role,
        )


class FakeCrawlerTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue(self, task_name: str) -> str:
        self.enqueued.append(task_name)
        return f"celery-{task_name}"


def make_test_client(
    auth_use_cases: FakeAuthUseCases | None = None,
    crawler_task_queue: FakeCrawlerTaskQueue | None = None,
) -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app()
    if auth_use_cases is not None:
        app.dependency_overrides[get_auth_use_cases] = lambda: auth_use_cases
    if crawler_task_queue is not None:
        app.dependency_overrides[get_crawler_task_queue] = lambda: crawler_task_queue

    def override_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    return TestClient(app), session_factory


def seed_crawler_run_logs(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        first = CrawlerRunLog(
            id="run-1",
            task_name="crawl_hot_deals_mock",
            status="succeeded",
            scanned_count=2,
            fetched_count=0,
            accepted_count=2,
            created_count=2,
            duplicate_count=0,
            skipped_count=0,
            skip_reasons_json={},
            error_type=None,
            error_message=None,
            started_at=NOW,
            finished_at=NOW,
            created_at=NOW,
            updated_at=NOW,
        )
        second = CrawlerRunLog(
            id="run-2",
            task_name="crawl_live_urls",
            status="succeeded",
            scanned_count=2,
            fetched_count=1,
            accepted_count=1,
            created_count=1,
            duplicate_count=0,
            skipped_count=1,
            skip_reasons_json={"host_rate_limited": 1},
            error_type=None,
            error_message=None,
            started_at=NOW + timedelta(minutes=1),
            finished_at=NOW + timedelta(minutes=1),
            created_at=NOW + timedelta(minutes=1),
            updated_at=NOW + timedelta(minutes=1),
        )
        session.add_all([first, second])
        session.commit()
    finally:
        session.close()


def test_admin_crawler_run_logs_require_bearer_token() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_crawler_run_logs(session_factory)

    response = client.get("/api/v1/admin/crawler-runs")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_crawler_run_logs_require_admin_role() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases(role="USER"))
    seed_crawler_run_logs(session_factory)

    response = client.get(
        "/api/v1/admin/crawler-runs",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_list_crawler_run_logs_newest_first_with_cursor() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    seed_crawler_run_logs(session_factory)

    first_page = client.get(
        "/api/v1/admin/crawler-runs?limit=1",
        headers={"Authorization": "Bearer access-1"},
    )
    second_page = client.get(
        "/api/v1/admin/crawler-runs?limit=1&cursor=run-2",
        headers={"Authorization": "Bearer access-1"},
    )

    assert first_page.status_code == 200
    assert first_page.json() == {
        "items": [
            {
                "id": "run-2",
                "taskName": "crawl_live_urls",
                "status": "succeeded",
                "scanned": 2,
                "fetched": 1,
                "accepted": 1,
                "created": 1,
                "duplicates": 0,
                "skipped": 1,
                "skipReasons": {"host_rate_limited": 1},
                "errorType": None,
                "errorMessage": None,
                "startedAt": "2026-06-03T01:01:00Z",
                "finishedAt": "2026-06-03T01:01:00Z",
                "createdAt": "2026-06-03T01:01:00Z",
            }
        ],
        "nextCursor": "run-2",
    }
    assert second_page.status_code == 200
    assert second_page.json()["items"][0]["id"] == "run-1"
    assert second_page.json()["nextCursor"] is None


def test_admin_can_list_failed_crawler_run_log_failure_fields() -> None:
    client, session_factory = make_test_client(FakeAuthUseCases())
    session = session_factory()
    try:
        session.add(
            CrawlerRunLog(
                id="run-failed",
                task_name="crawl_live_urls",
                status="failed",
                scanned_count=1,
                fetched_count=0,
                accepted_count=0,
                created_count=0,
                duplicate_count=0,
                skipped_count=0,
                skip_reasons_json={},
                error_type="RuntimeError",
                error_message="crawler fetch failed",
                started_at=NOW,
                finished_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.get(
        "/api/v1/admin/crawler-runs",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "failed"
    assert response.json()["items"][0]["errorType"] == "RuntimeError"
    assert response.json()["items"][0]["errorMessage"] == "crawler fetch failed"


def test_admin_crawler_run_trigger_requires_bearer_token() -> None:
    queue = FakeCrawlerTaskQueue()
    client, _ = make_test_client(FakeAuthUseCases(), crawler_task_queue=queue)

    response = client.post(
        "/api/v1/admin/crawler-runs/trigger",
        json={"taskName": "crawl_live_urls"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert queue.enqueued == []


def test_admin_crawler_run_trigger_requires_admin_role() -> None:
    queue = FakeCrawlerTaskQueue()
    client, _ = make_test_client(FakeAuthUseCases(role="USER"), crawler_task_queue=queue)

    response = client.post(
        "/api/v1/admin/crawler-runs/trigger",
        headers={"Authorization": "Bearer access-1"},
        json={"taskName": "crawl_live_urls"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert queue.enqueued == []


def test_admin_can_trigger_allowlisted_crawler_task() -> None:
    queue = FakeCrawlerTaskQueue()
    client, _ = make_test_client(FakeAuthUseCases(), crawler_task_queue=queue)

    response = client.post(
        "/api/v1/admin/crawler-runs/trigger",
        headers={"Authorization": "Bearer access-1"},
        json={"taskName": "crawl_live_urls"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "taskName": "crawl_live_urls",
        "celeryTaskId": "celery-crawl_live_urls",
    }
    assert queue.enqueued == ["crawl_live_urls"]


def test_admin_crawler_run_trigger_rejects_unknown_task_name() -> None:
    queue = FakeCrawlerTaskQueue()
    client, _ = make_test_client(FakeAuthUseCases(), crawler_task_queue=queue)

    response = client.post(
        "/api/v1/admin/crawler-runs/trigger",
        headers={"Authorization": "Bearer access-1"},
        json={"taskName": "delete_everything"},
    )

    assert response.status_code == 422
    assert queue.enqueued == []
