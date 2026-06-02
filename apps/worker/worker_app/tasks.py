from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.db.session import create_session_factory
from app.modules.auth.models import User
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.favorites.repository import FavoritesRepository
from app.modules.notifications.generation import (
    NotificationGenerationUseCases,
    ScheduledNotificationUseCases,
)
from app.modules.notifications.repository import NotificationsRepository
from app.modules.products.repository import ProductRepository
from app.modules.submissions.repository import SubmissionsRepository
from app.modules.submissions.schemas import SubmissionCreateRequest
from app.modules.submissions.use_cases import SubmissionsUseCases
from sqlalchemy.orm import Session

from worker_app.celery_app import celery_app
from worker_app.config import WorkerSettings
from worker_app.crawler_http import CrawlFetchResult, SafeCrawlerHttpClient
from worker_app.crawler_parsers import CrawlerParserRegistry, parse_source_parsers
from worker_app.crawler_rate_limits import CrawlerHostRunLimiter
from worker_app.crawler_sources import CrawlerRawItem, CrawlerSourceRegistry, parse_source_profiles

CRAWLER_RAW_ITEMS: list[CrawlerRawItem] = [
    CrawlerRawItem.model_validate(
        {
            "offerType": "deal",
            "sourceUrl": "https://mock.example.com/deals/galaxy-s26-launch",
            "productName": "Galaxy S26",
            "brand": "Samsung",
            "modelName": "SM-S260",
            "category": "smartphone",
            "title": "Galaxy S26 launch deal",
            "seller": "Mock Hotdeal",
            "originalPrice": 1400000,
            "salePrice": 1090000,
            "currentPrice": None,
            "currency": "KRW",
        }
    ),
    CrawlerRawItem.model_validate(
        {
            "offerType": "auction",
            "sourceUrl": "https://mock.example.com/auctions/galaxy-s26-sealed",
            "productName": "Galaxy S26",
            "brand": "Samsung",
            "modelName": "SM-S260",
            "category": "smartphone",
            "title": "Galaxy S26 sealed auction",
            "seller": "Mock Auction",
            "originalPrice": None,
            "salePrice": None,
            "currentPrice": 720000,
            "currency": "KRW",
        }
    ),
]


FetchText = Callable[[str], CrawlFetchResult]


@celery_app.task(name="dealmoa.crawl_hot_deals_mock")  # type: ignore[untyped-decorator]
def crawl_hot_deals_mock(now_iso: str | None = None) -> dict[str, object]:
    settings = WorkerSettings()
    now = parse_task_datetime(now_iso)
    source_registry = CrawlerSourceRegistry(parse_source_profiles(settings.crawler_source_profiles))
    session_factory = create_session_factory(settings.database_url)
    session: Session = session_factory()
    try:
        actor = ensure_crawler_user(session=session, settings=settings, now=now)
        use_cases = SubmissionsUseCases(
            submissions_repository=SubmissionsRepository(session),
            product_repository=ProductRepository(session),
            domain_events=DomainEventsUseCases(
                repository=DomainEventsRepository(session),
                now=lambda: now,
            ),
            now=lambda: now,
        )
        accepted_count = 0
        created_count = 0
        duplicate_count = 0
        skipped_count = 0
        for raw_item in CRAWLER_RAW_ITEMS:
            item = source_registry.parse(raw_item)
            if item is None:
                skipped_count += 1
                continue
            accepted_count += 1
            result = use_cases.create_submission(
                actor=actor,
                request=SubmissionCreateRequest.model_validate(item),
            )
            if result.created:
                created_count += 1
            else:
                duplicate_count += 1
        session.commit()
        return {
            "task": "crawl_hot_deals_mock",
            "scanned": len(CRAWLER_RAW_ITEMS),
            "accepted": accepted_count,
            "created": created_count,
            "duplicates": duplicate_count,
            "skipped": skipped_count,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(name="dealmoa.crawl_live_urls")  # type: ignore[untyped-decorator]
def crawl_live_urls(now_iso: str | None = None) -> dict[str, object]:
    settings = WorkerSettings()
    urls = parse_csv(settings.crawler_live_urls)
    if not urls:
        return live_crawler_summary(scanned=0)
    client = SafeCrawlerHttpClient(
        timeout_seconds=settings.crawler_http_timeout_seconds,
        max_bytes=settings.crawler_http_max_bytes,
        user_agent=settings.crawler_user_agent,
    )
    return execute_live_crawler(now_iso=now_iso, urls=urls, fetcher=client.fetch_text)


def execute_live_crawler(
    *,
    now_iso: str | None,
    urls: list[str],
    fetcher: FetchText,
) -> dict[str, object]:
    settings = WorkerSettings()
    now = parse_task_datetime(now_iso)
    source_registry = CrawlerSourceRegistry(parse_source_profiles(settings.crawler_source_profiles))
    parser_registry = CrawlerParserRegistry(parse_source_parsers(settings.crawler_source_parsers))
    host_limiter = CrawlerHostRunLimiter(max_urls_per_host=settings.crawler_max_urls_per_host)
    session_factory = create_session_factory(settings.database_url)
    session: Session = session_factory()
    fetched_count = 0
    accepted_count = 0
    created_count = 0
    duplicate_count = 0
    skipped_count = 0
    skip_reasons: dict[str, int] = {}
    try:
        actor = ensure_crawler_user(session=session, settings=settings, now=now)
        use_cases = SubmissionsUseCases(
            submissions_repository=SubmissionsRepository(session),
            product_repository=ProductRepository(session),
            domain_events=DomainEventsUseCases(
                repository=DomainEventsRepository(session),
                now=lambda: now,
            ),
            now=lambda: now,
        )
        for url in urls:
            if not source_registry.allows_url(url):
                skipped_count += 1
                increment_skip_reason(skip_reasons, "source_not_allowed")
                continue
            if not host_limiter.allow(url):
                skipped_count += 1
                increment_skip_reason(skip_reasons, "host_rate_limited")
                continue
            fetched = fetcher(url)
            if fetched.status != "fetched" or fetched.text is None:
                skipped_count += 1
                increment_skip_reason(skip_reasons, fetched.reason or "fetch_failed")
                continue
            fetched_count += 1
            raw_item, parser_skip_reason = parser_registry.parse(source_url=url, html=fetched.text)
            if raw_item is None:
                skipped_count += 1
                increment_skip_reason(skip_reasons, parser_skip_reason or "parse_failed")
                continue
            item = source_registry.parse(raw_item)
            if item is None:
                skipped_count += 1
                increment_skip_reason(skip_reasons, "source_not_allowed")
                continue
            accepted_count += 1
            result = use_cases.create_submission(
                actor=actor,
                request=SubmissionCreateRequest.model_validate(item),
            )
            if result.created:
                created_count += 1
            else:
                duplicate_count += 1
        session.commit()
        return live_crawler_summary(
            scanned=len(urls),
            fetched=fetched_count,
            accepted=accepted_count,
            created=created_count,
            duplicates=duplicate_count,
            skipped=skipped_count,
            skip_reasons=skip_reasons,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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


def parse_csv(value: str) -> list[str]:
    return [entry.strip() for entry in value.split(",") if entry.strip()]


def increment_skip_reason(skip_reasons: dict[str, int], reason: str) -> None:
    skip_reasons[reason] = skip_reasons.get(reason, 0) + 1


def live_crawler_summary(
    *,
    scanned: int,
    fetched: int = 0,
    accepted: int = 0,
    created: int = 0,
    duplicates: int = 0,
    skipped: int = 0,
    skip_reasons: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "task": "crawl_live_urls",
        "scanned": scanned,
        "fetched": fetched,
        "accepted": accepted,
        "created": created,
        "duplicates": duplicates,
        "skipped": skipped,
        "skipReasons": skip_reasons or {},
    }


def ensure_crawler_user(
    *,
    session: Session,
    settings: WorkerSettings,
    now: datetime,
) -> AuthenticatedUser:
    user = session.get(User, settings.crawler_system_user_id)
    if user is None:
        user = User(
            id=settings.crawler_system_user_id,
            email=settings.crawler_system_user_email,
            nickname=settings.crawler_system_user_nickname,
            role="USER",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.flush()
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        nickname=user.nickname or settings.crawler_system_user_nickname,
        role=user.role,
    )


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
