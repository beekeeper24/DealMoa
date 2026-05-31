from datetime import UTC, datetime, timedelta

from app.db.session import create_session_factory
from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.generation import (
    NotificationGenerationUseCases,
    ScheduledNotificationUseCases,
)
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.repository import ProductRepository
from sqlalchemy.orm import Session

from worker_app.celery_app import celery_app
from worker_app.config import WorkerSettings


@celery_app.task(name="dealmoa.crawl_hot_deals_mock")  # type: ignore[untyped-decorator]
def crawl_hot_deals_mock() -> dict[str, object]:
    return {"task": "crawl_hot_deals_mock", "created": 0}


@celery_app.task(name="dealmoa.ai_review_submission_mock")  # type: ignore[untyped-decorator]
def ai_review_submission_mock(submission_id: str) -> dict[str, object]:
    return {
        "task": "ai_review_submission_mock",
        "submissionId": submission_id,
        "decision": "needs_admin_review",
        "reason": "mock review passed: admin approval required",
    }


@celery_app.task(name="dealmoa.rebuild_search_index")  # type: ignore[untyped-decorator]
def rebuild_search_index() -> dict[str, object]:
    return {
        "task": "rebuild_search_index",
        "products": 0,
        "deals": 0,
        "auctions": 0,
    }


def parse_task_datetime(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@celery_app.task(name="dealmoa.generate_auction_ending_soon_notifications")  # type: ignore[untyped-decorator]
def generate_auction_ending_soon_notifications(now_iso: str | None = None) -> dict[str, object]:
    settings = WorkerSettings()
    now = parse_task_datetime(now_iso)
    session_factory = create_session_factory(settings.database_url)
    session: Session = session_factory()
    try:
        use_cases = ScheduledNotificationUseCases(
            product_repository=ProductRepository(session),
            notification_generation=NotificationGenerationUseCases(
                favorites_repository=FavoritesRepository(session),
                notifications_repository=NotificationsRepository(session),
                now=lambda: now,
            ),
            now=lambda: now,
        )
        summary = use_cases.generate_auction_ending_soon_notifications(
            lookahead=timedelta(minutes=settings.auction_ending_soon_lookahead_minutes),
            limit=settings.auction_ending_soon_batch_size,
        )
        session.commit()
        return {
            "task": "generate_auction_ending_soon_notifications",
            "scannedAuctions": summary.scanned_auction_count,
            "createdNotifications": summary.created_notification_count,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
