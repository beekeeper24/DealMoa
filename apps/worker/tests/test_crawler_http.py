import httpx
from worker_app.crawler_http import CrawlFetchResult, SafeCrawlerHttpClient

PUBLIC_TEST_IP = "93.184.216.34"


def test_client_rejects_non_http_urls_before_network() -> None:
    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=100,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: [PUBLIC_TEST_IP],
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
        return httpx.Response(
            200,
            text="<html><title>blocked</title></html>",
            headers={"Content-Type": "text/html"},
        )

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=1_000,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: [PUBLIC_TEST_IP],
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
        resolver=lambda host: [PUBLIC_TEST_IP],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result == CrawlFetchResult(status="skipped", reason="response_too_large")


def test_client_rejects_non_html_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, json={"title": "not html"})

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=1_000,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: [PUBLIC_TEST_IP],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result == CrawlFetchResult(status="skipped", reason="unsupported_content_type")


def test_client_returns_text_for_safe_html_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="<html><title>ok</title></html>",
            headers={"Content-Type": "text/html"},
        )

    client = SafeCrawlerHttpClient(
        timeout_seconds=5.0,
        max_bytes=1_000,
        user_agent="DealMoaBot/0.1",
        resolver=lambda host: [PUBLIC_TEST_IP],
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch_text("https://example.com/deal/1")

    assert result.status == "fetched"
    assert result.reason is None
    assert result.text == "<html><title>ok</title></html>"
