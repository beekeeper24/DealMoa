# Live Crawler Fetch Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add the first live HTTP crawler task with SSRF-safe URL validation, robots.txt checks, response limits, and a minimal parser boundary while preserving safe local and CI defaults.

**Architecture:** Keep live crawling inside `apps/worker`; FastAPI remains uninvolved. The task starts from configured URLs, checks source profiles before network access, fetches through a safe client, parses only bounded HTML into `CrawlerRawItem`, then reuses the existing submission intake path so crawler output remains `pending_review`. Default `CRAWLER_LIVE_URLS` is empty, so local and CI runs do not perform external network calls.

**Tech Stack:** Python 3.12, Celery, Pydantic Settings, httpx with MockTransport tests, stdlib `ipaddress`, `socket`, `urllib.robotparser`, `html.parser`, pytest, ruff, mypy.

---

## File Structure

- Modify: `apps/worker/pyproject.toml`
  - Add `httpx>=0.28.1` to worker dependencies.
- Modify: `apps/worker/worker_app/config.py`
  - Add live crawler settings: `CRAWLER_LIVE_URLS`, `CRAWLER_HTTP_TIMEOUT_SECONDS`, `CRAWLER_HTTP_MAX_BYTES`, `CRAWLER_USER_AGENT`.
- Modify: `.env.example`
  - Document live crawler settings with safe defaults.
- Modify: `docker-compose.yml`
  - Pass live crawler settings to `worker` and `worker-beat`.
- Modify: `apps/worker/worker_app/crawler_sources.py`
  - Add a URL-level source profile check so unknown or blocked hosts can be skipped before HTTP fetch.
- Create: `apps/worker/worker_app/crawler_http.py`
  - Own SSRF-safe URL validation, DNS/IP checks, robots.txt fetch/parse, bounded HTTP GET, and stable skip reasons.
- Create: `apps/worker/worker_app/crawler_parsers.py`
  - Own minimal bounded HTML parsing into `CrawlerRawItem`.
- Modify: `apps/worker/worker_app/tasks.py`
  - Register `dealmoa.crawl_live_urls` and route accepted parsed items through `SubmissionsUseCases`.
- Create: `apps/worker/tests/test_crawler_http.py`
  - Unit tests for URL validation, private IP blocking, robots policy, content type, response size, and timeout/error skip behavior.
- Create: `apps/worker/tests/test_crawler_parsers.py`
  - Unit tests for minimal HTML parser behavior.
- Modify: `apps/worker/tests/test_crawler_sources.py`
  - Cover pre-fetch URL allow/block checks.
- Modify: `apps/worker/tests/test_tasks.py`
  - Cover task registration, empty URL default summary, and injected live fetch helper idempotency.
- Modify: `docs/async-events.md`, `docs/security-abuse.md`, `docs/submissions.md`, `docs/handoff.md`
  - Document live crawler boundary, safe defaults, skipped network cases, and deferred parser/source reputation storage.

---

## Task 1: Worker Live Crawler Settings

**Files:**
- Modify: `apps/worker/pyproject.toml`
- Modify: `apps/worker/worker_app/config.py`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Test: `apps/worker/tests/test_tasks.py`

- [x] **Step 1: Write the failing settings expectations**

Add a focused test to `apps/worker/tests/test_tasks.py` or a new `apps/worker/tests/test_worker_config.py`:

```python
from worker_app.config import WorkerSettings


def test_live_crawler_settings_default_to_no_external_fetch(monkeypatch) -> None:
    monkeypatch.delenv("CRAWLER_LIVE_URLS", raising=False)
    settings = WorkerSettings()

    assert settings.crawler_live_urls == ""
    assert settings.crawler_http_timeout_seconds == 5.0
    assert settings.crawler_http_max_bytes == 1_048_576
    assert settings.crawler_user_agent == "DealMoaBot/0.1 (+https://dealmoa.local/crawler)"
```

- [x] **Step 2: Run the failing test**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_worker_config.py -q
```

Expected: fail because the new settings do not exist yet.

- [x] **Step 3: Add dependencies and settings**

Update `apps/worker/pyproject.toml`:

```toml
dependencies = [
    "celery[redis]>=5.5.3",
    "httpx>=0.28.1",
    "pydantic-settings>=2.11.0",
]
```

Add fields to `WorkerSettings` in `apps/worker/worker_app/config.py`:

```python
crawler_live_urls: str = Field(
    default="",
    validation_alias="CRAWLER_LIVE_URLS",
)
crawler_http_timeout_seconds: float = Field(
    default=5.0,
    validation_alias="CRAWLER_HTTP_TIMEOUT_SECONDS",
)
crawler_http_max_bytes: int = Field(
    default=1_048_576,
    validation_alias="CRAWLER_HTTP_MAX_BYTES",
)
crawler_user_agent: str = Field(
    default="DealMoaBot/0.1 (+https://dealmoa.local/crawler)",
    validation_alias="CRAWLER_USER_AGENT",
)
```

Add matching `.env.example` entries:

```dotenv
CRAWLER_LIVE_URLS=
CRAWLER_HTTP_TIMEOUT_SECONDS=5
CRAWLER_HTTP_MAX_BYTES=1048576
CRAWLER_USER_AGENT=DealMoaBot/0.1 (+https://dealmoa.local/crawler)
```

Pass the same values to `worker` and `worker-beat` in `docker-compose.yml`.

- [x] **Step 4: Verify settings pass**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_worker_config.py -q
```

Expected: pass.

---

## Task 2: Pre-Fetch Source Profile Gate

**Files:**
- Modify: `apps/worker/worker_app/crawler_sources.py`
- Modify: `apps/worker/tests/test_crawler_sources.py`

- [x] **Step 1: Write failing source URL tests**

Append to `apps/worker/tests/test_crawler_sources.py`:

```python
def test_registry_allows_url_before_fetch_only_for_allowed_profiles() -> None:
    registry = CrawlerSourceRegistry(
        [
            CrawlerSourceProfile(host="mock.example.com", reputation="trusted", action="allow"),
            CrawlerSourceProfile(host="blocked.example.com", reputation="low", action="block"),
        ]
    )

    assert registry.allows_url("https://mock.example.com/deals/1") is True
    assert registry.allows_url("https://blocked.example.com/deals/1") is False
    assert registry.allows_url("https://unknown.example.com/deals/1") is False
```

- [x] **Step 2: Run the failing test**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_sources.py::test_registry_allows_url_before_fetch_only_for_allowed_profiles -q
```

Expected: fail because `allows_url` does not exist.

- [x] **Step 3: Add URL-level source gate**

Add this method to `CrawlerSourceRegistry`:

```python
def allows_url(self, source_url: str) -> bool:
    host = urlparse(source_url).netloc.casefold()
    profile = self.profiles_by_host.get(host)
    return profile is not None and profile.action == "allow"
```

- [x] **Step 4: Verify source tests pass**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_sources.py -q
```

Expected: pass.

---

## Task 3: SSRF-Safe HTTP Client

**Files:**
- Create: `apps/worker/worker_app/crawler_http.py`
- Create: `apps/worker/tests/test_crawler_http.py`

- [x] **Step 1: Write failing HTTP safety tests**

Create `apps/worker/tests/test_crawler_http.py`:

```python
import socket

import httpx

from worker_app.crawler_http import CrawlFetchResult, SafeCrawlerHttpClient


def test_client_rejects_non_http_urls_before_network() -> None:
    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=100,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: ["203.0.113.10"],
    )

    result = client.fetch_text("file:///etc/passwd")

    assert result == CrawlFetchResult(status="skipped", reason="unsupported_scheme")


def test_client_rejects_private_resolved_ip_before_network() -> None:
    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=100,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: ["127.0.0.1"],
    )

    result = client.fetch_text("https://example.com/deal")

    assert result == CrawlFetchResult(status="skipped", reason="unsafe_resolved_ip")


def test_client_respects_robots_disallow() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /deal")
        return httpx.Response(200, text="<html><title>blocked</title></html>")

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=1_000,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: ["203.0.113.10"],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result == CrawlFetchResult(status="skipped", reason="robots_disallow")
    assert [request.url.path for request in requests] == ["/robots.txt"]


def test_client_enforces_response_size_limit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text="x" * 101, headers={"Content-Type": "text/html"})

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=100,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: ["203.0.113.10"],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result == CrawlFetchResult(status="skipped", reason="response_too_large")


def test_client_returns_text_for_safe_html_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text="<html><title>ok</title></html>", headers={"Content-Type": "text/html"})

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=1_000,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: ["203.0.113.10"],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result.status == "fetched"
    assert result.reason is None
    assert result.text == "<html><title>ok</title></html>"
```

- [x] **Step 2: Run the failing tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_http.py -q
```

Expected: fail because `crawler_http.py` does not exist.

- [x] **Step 3: Implement safe HTTP client**

Create `apps/worker/worker_app/crawler_http.py` with:

```python
from collections.abc import Callable
from dataclasses import dataclass
from ipaddress import ip_address
import socket
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


@dataclass(frozen=True)
class CrawlFetchResult:
    status: str
    reason: str | None = None
    text: str | None = None


Resolver = Callable[[str], list[str]]


class SafeCrawlerHttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        max_bytes: int,
        user_agent: str,
        resolver: Resolver | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.user_agent = user_agent
        self.resolver = resolver or resolve_host_ips
        self.transport = transport

    def fetch_text(self, url: str) -> CrawlFetchResult:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return CrawlFetchResult(status="skipped", reason="unsupported_scheme")
        if not parsed.hostname:
            return CrawlFetchResult(status="skipped", reason="missing_host")
        if parsed.username or parsed.password:
            return CrawlFetchResult(status="skipped", reason="userinfo_not_allowed")
        if not self._host_is_safe(parsed.hostname):
            return CrawlFetchResult(status="skipped", reason="unsafe_resolved_ip")
        if not self._robots_allows(url):
            return CrawlFetchResult(status="skipped", reason="robots_disallow")
        return self._fetch_html(url)

    def _host_is_safe(self, host: str) -> bool:
        try:
            resolved_ips = self.resolver(host)
        except OSError:
            return False
        if not resolved_ips:
            return False
        return all(ip_is_public(ip) for ip in resolved_ips)

    def _robots_allows(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            with self._client() as client:
                response = client.get(robots_url)
        except httpx.HTTPError:
            return False
        if response.status_code >= 400:
            return True
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(self.user_agent, url)

    def _fetch_html(self, url: str) -> CrawlFetchResult:
        try:
            with self._client() as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPError:
            return CrawlFetchResult(status="skipped", reason="http_error")
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower():
            return CrawlFetchResult(status="skipped", reason="unsupported_content_type")
        body = response.content
        if len(body) > self.max_bytes:
            return CrawlFetchResult(status="skipped", reason="response_too_large")
        return CrawlFetchResult(status="fetched", text=body.decode(response.encoding or "utf-8", errors="replace"))

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": self.user_agent},
            transport=self.transport,
        )


def resolve_host_ips(host: str) -> list[str]:
    return list(
        {
            sockaddr[0]
            for _, _, _, _, sockaddr in socket.getaddrinfo(
                host,
                None,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        }
    )


def ip_is_public(value: str) -> bool:
    parsed = ip_address(value)
    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )
```

- [x] **Step 4: Verify HTTP safety tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_http.py -q
```

Expected: pass.

---

## Task 4: Minimal HTML Parser Boundary

**Files:**
- Create: `apps/worker/worker_app/crawler_parsers.py`
- Create: `apps/worker/tests/test_crawler_parsers.py`

- [x] **Step 1: Write failing parser tests**

Create `apps/worker/tests/test_crawler_parsers.py`:

```python
from worker_app.crawler_parsers import parse_live_deal_html


def test_parser_extracts_minimum_live_deal_payload() -> None:
    raw_item = parse_live_deal_html(
        source_url="https://mock.example.com/deals/1",
        html="""
        <html>
          <head><title>Galaxy S26 launch deal</title></head>
          <body>
            <article
              data-dealmoa-offer-type="deal"
              data-dealmoa-product-name="Galaxy S26"
              data-dealmoa-brand="Samsung"
              data-dealmoa-model-name="SM-S260"
              data-dealmoa-category="smartphone"
              data-dealmoa-title="Galaxy S26 launch deal"
              data-dealmoa-seller="Mock Hotdeal"
              data-dealmoa-original-price="1400000"
              data-dealmoa-sale-price="1090000"
              data-dealmoa-currency="KRW"
            ></article>
          </body>
        </html>
        """,
    )

    assert raw_item.source_url == "https://mock.example.com/deals/1"
    assert raw_item.offer_type == "deal"
    assert raw_item.product_name == "Galaxy S26"
    assert raw_item.sale_price == 1_090_000
    assert raw_item.current_price is None


def test_parser_returns_none_when_required_fields_are_missing() -> None:
    assert parse_live_deal_html(source_url="https://mock.example.com/deals/1", html="<html></html>") is None
```

- [x] **Step 2: Run the failing parser tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_parsers.py -q
```

Expected: fail because `crawler_parsers.py` does not exist.

- [x] **Step 3: Implement minimal parser**

Create `apps/worker/worker_app/crawler_parsers.py` with:

```python
from html.parser import HTMLParser

from pydantic import ValidationError

from worker_app.crawler_sources import CrawlerRawItem


class DealMoaArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.article_attrs: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "article" or self.article_attrs is not None:
            return
        parsed_attrs = {key: value for key, value in attrs if value is not None}
        if "data-dealmoa-product-name" in parsed_attrs:
            self.article_attrs = parsed_attrs


def parse_live_deal_html(*, source_url: str, html: str) -> CrawlerRawItem | None:
    parser = DealMoaArticleParser()
    parser.feed(html)
    attrs = parser.article_attrs
    if attrs is None:
        return None
    try:
        return CrawlerRawItem.model_validate(
            {
                "offerType": attrs.get("data-dealmoa-offer-type", "deal"),
                "sourceUrl": source_url,
                "productName": attrs.get("data-dealmoa-product-name"),
                "brand": attrs.get("data-dealmoa-brand"),
                "modelName": attrs.get("data-dealmoa-model-name"),
                "category": attrs.get("data-dealmoa-category"),
                "title": attrs.get("data-dealmoa-title"),
                "seller": attrs.get("data-dealmoa-seller"),
                "originalPrice": int_or_none(attrs.get("data-dealmoa-original-price")),
                "salePrice": int_or_none(attrs.get("data-dealmoa-sale-price")),
                "currentPrice": int_or_none(attrs.get("data-dealmoa-current-price")),
                "currency": attrs.get("data-dealmoa-currency", "KRW"),
            }
        )
    except (TypeError, ValueError, ValidationError):
        return None


def int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
```

- [x] **Step 4: Verify parser tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_parsers.py -q
```

Expected: pass.

---

## Task 5: Live Crawler Task Wiring

**Files:**
- Modify: `apps/worker/worker_app/tasks.py`
- Modify: `apps/worker/tests/test_tasks.py`

- [x] **Step 1: Write failing task tests**

Add to `apps/worker/tests/test_tasks.py`:

```python
def test_initial_celery_tasks_are_registered() -> None:
    assert "dealmoa.crawl_hot_deals_mock" in celery_app.tasks
    assert "dealmoa.crawl_live_urls" in celery_app.tasks
    assert "dealmoa.ai_review_submission_mock" in celery_app.tasks
    assert "dealmoa.rebuild_search_index" in celery_app.tasks
    assert "dealmoa.generate_auction_ending_soon_notifications" in celery_app.tasks


def test_live_crawler_task_defaults_to_no_external_fetch(monkeypatch) -> None:
    monkeypatch.delenv("CRAWLER_LIVE_URLS", raising=False)

    assert crawl_live_urls(now_iso="2026-06-02T00:00:00+00:00") == {
        "task": "crawl_live_urls",
        "scanned": 0,
        "fetched": 0,
        "accepted": 0,
        "created": 0,
        "duplicates": 0,
        "skipped": 0,
        "skipReasons": {},
    }
```

Also add an injected helper test after implementation shape is introduced:

```python
def test_execute_live_crawler_ingests_allowed_fetched_html(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'dealmoa-live-crawler-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("CRAWLER_SOURCE_PROFILES", "mock.example.com:trusted:allow")

    from app.db.base import Base
    from app.modules.submissions.models import Submission
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from worker_app.crawler_http import CrawlFetchResult
    from worker_app.tasks import execute_live_crawler

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    def fetcher(url: str) -> CrawlFetchResult:
        return CrawlFetchResult(
            status="fetched",
            text=\"\"\"
            <article
              data-dealmoa-offer-type="deal"
              data-dealmoa-product-name="Galaxy S26"
              data-dealmoa-title="Galaxy S26 launch deal"
              data-dealmoa-sale-price="1090000"
              data-dealmoa-currency="KRW"
            ></article>
            \"\"\",
        )

    summary = execute_live_crawler(
        now_iso="2026-06-02T00:00:00+00:00",
        urls=["https://mock.example.com/deals/1"],
        fetcher=fetcher,
    )

    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        submissions = list(session.scalars(select(Submission)))
    finally:
        session.close()

    assert summary["created"] == 1
    assert summary["accepted"] == 1
    assert summary["fetched"] == 1
    assert len(submissions) == 1
    assert submissions[0].status == "pending_review"
```

- [x] **Step 2: Run the failing task tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_tasks.py -q
```

Expected: fail because `crawl_live_urls` and `execute_live_crawler` do not exist.

- [x] **Step 3: Implement task and helper**

In `apps/worker/worker_app/tasks.py`:

```python
from collections.abc import Callable

from worker_app.crawler_http import CrawlFetchResult, SafeCrawlerHttpClient
from worker_app.crawler_parsers import parse_live_deal_html
```

Add:

```python
FetchText = Callable[[str], CrawlFetchResult]


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
            fetched = fetcher(url)
            if fetched.status != "fetched" or fetched.text is None:
                skipped_count += 1
                increment_skip_reason(skip_reasons, fetched.reason or "fetch_failed")
                continue
            fetched_count += 1
            raw_item = parse_live_deal_html(source_url=url, html=fetched.text)
            if raw_item is None:
                skipped_count += 1
                increment_skip_reason(skip_reasons, "parse_failed")
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
```

- [x] **Step 4: Verify task tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_tasks.py -q
```

Expected: pass.

---

## Task 6: Documentation And Security Review

**Files:**
- Modify: `docs/async-events.md`
- Modify: `docs/security-abuse.md`
- Modify: `docs/submissions.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Update async crawler docs**

Document:

- `dealmoa.crawl_live_urls` is disabled by default because `CRAWLER_LIVE_URLS` defaults to empty.
- URLs must pass `CRAWLER_SOURCE_PROFILES` before network fetch.
- HTTP fetch blocks private/reserved IPs, userinfo URLs, non-http schemes, disallowed robots paths, non-HTML content, and over-limit responses.
- Successful fetches still create only `pending_review` submissions.

- [x] **Step 2: Update security docs**

Add the security boundary:

- Source allowlists do not replace SSRF checks.
- Robots.txt failures are conservative skips.
- Redirects are not followed in the first live crawler pass.
- Response bodies are capped by `CRAWLER_HTTP_MAX_BYTES`.
- Parsed content is still untrusted UGC and requires AI first-pass plus admin approval.

- [x] **Step 3: Update handoff docs**

Move `live HTTP crawler fetch hardening` from deferred to completed scope and keep these deferred:

- source-specific parser plugins;
- persistent source reputation storage;
- production crawl scheduling;
- crawler log/admin UI;
- crawl rate-limiting per host.

- [x] **Step 4: Run focused security review checks**

Run:

```bash
rg -n "follow_redirects|robots|private|loopback|link_local|multicast|reserved|CRAWLER_LIVE_URLS|CRAWLER_HTTP_MAX_BYTES|fetch_text|allows_url|create_submission" apps/worker docs
```

Expected:

- `allows_url` appears before live fetch in task code.
- `fetch_text` uses `follow_redirects=False`.
- docs mention source allowlist plus SSRF-safe checks.
- `create_submission` happens only after source gate, safe fetch, parser, and source registry parse.

---

## Task 7: Full Verification And PR

**Files:**
- All changed files

- [x] **Step 1: Run worker-focused tests**

Run:

```bash
PYTHONPATH=apps/api:apps/worker uv run pytest apps/worker/tests/test_crawler_sources.py apps/worker/tests/test_crawler_http.py apps/worker/tests/test_crawler_parsers.py apps/worker/tests/test_tasks.py -q
```

Expected: all pass.

- [x] **Step 2: Run Python lint/type checks**

Run:

```bash
uv run ruff check apps/api apps/consumer apps/worker
MYPYPATH=apps/api:apps/consumer:apps/worker uv run mypy apps/api/app apps/api/tests apps/consumer/consumer_app apps/consumer/tests apps/worker/worker_app apps/worker/tests
```

Expected: both pass.

- [x] **Step 3: Run full backend/consumer/worker tests**

Run:

```bash
PYTHONPATH=apps/api:apps/consumer:apps/worker uv run pytest apps/api/tests apps/consumer/tests apps/worker/tests -q
```

Expected: all pass.

- [x] **Step 4: Run Docker Compose config check**

Run:

```bash
docker compose --profile core --profile worker config
```

Expected: config renders worker live crawler environment variables.

- [x] **Step 5: Run web verification because shared CI should stay green**

Run:

```bash
corepack pnpm --filter @dealmoa/web lint
corepack pnpm --filter @dealmoa/web typecheck
corepack pnpm --filter @dealmoa/web test
corepack pnpm --filter @dealmoa/web build
corepack pnpm --filter @dealmoa/web exec playwright test
```

Expected: all pass.

- [x] **Step 6: Run diff check**

Run:

```bash
git diff --check
```

Expected: no output.

- [x] **Step 7: Commit and ship through Git Flow**

Use Korean commit message:

```bash
git add .env.example docker-compose.yml apps/worker docs
git commit -m "라이브 크롤러 HTTP 안전 경계 추가"
git push -u origin feature/live-crawler-fetch-hardening
gh pr create --base develop --head feature/live-crawler-fetch-hardening --title "라이브 크롤러 HTTP 안전 경계 추가"
gh pr checks --watch
gh pr merge --merge
git checkout develop
git pull --ff-only origin develop
```

Expected: PR merges to `develop`; remote feature branch remains unless the user explicitly asks to delete it.

---

## Self-Review

- Spec coverage: This plan covers safe defaults, pre-fetch source profile gate, SSRF-safe fetch, robots.txt, response size cap, minimal parser boundary, pending-review submission reuse, docs, security review, full verification, and Git Flow integration.
- Placeholder scan: No task uses TBD/TODO/fill-in placeholders. Each implementation task names exact files, commands, and expected behavior.
- Type consistency: `CrawlerRawItem`, `CrawlerSourceRegistry`, `SubmissionCreateRequest`, `WorkerSettings`, and task summary keys match existing worker conventions.
