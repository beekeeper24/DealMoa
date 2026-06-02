import http.client
import socket
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


@dataclass(frozen=True)
class CrawlFetchResult:
    status: str
    reason: str | None = None
    text: str | None = None


@dataclass(frozen=True)
class CrawlerHttpResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def header(self, name: str) -> str:
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return ""


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
        resolved_ip = self._safe_resolved_ip(parsed.hostname)
        if resolved_ip is None:
            return CrawlFetchResult(status="skipped", reason="unsafe_resolved_ip")
        if not self._robots_allows(url=url, resolved_ip=resolved_ip):
            return CrawlFetchResult(status="skipped", reason="robots_disallow")
        return self._fetch_html(url=url, resolved_ip=resolved_ip)

    def _safe_resolved_ip(self, host: str) -> str | None:
        try:
            resolved_ips = self.resolver(host)
        except OSError:
            return None
        if not resolved_ips:
            return None
        if not all(ip_is_public(ip) for ip in resolved_ips):
            return None
        return resolved_ips[0]

    def _robots_allows(self, *, url: str, resolved_ip: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            response = self._get(robots_url, resolved_ip=resolved_ip)
        except (CrawlerHttpError, httpx.HTTPError, OSError):
            return False
        if response.status_code >= 400:
            return True
        if response.status_code >= 300:
            return False
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(self.user_agent, url)

    def _fetch_html(self, *, url: str, resolved_ip: str) -> CrawlFetchResult:
        try:
            response = self._get(url, resolved_ip=resolved_ip)
        except (CrawlerHttpError, httpx.HTTPError, OSError):
            return CrawlFetchResult(status="skipped", reason="http_error")
        if response.status_code >= 300:
            return CrawlFetchResult(status="skipped", reason="http_error")
        content_type = response.header("Content-Type")
        if "text/html" not in content_type.lower():
            return CrawlFetchResult(status="skipped", reason="unsupported_content_type")
        body = response.content
        if len(body) > self.max_bytes:
            return CrawlFetchResult(status="skipped", reason="response_too_large")
        return CrawlFetchResult(status="fetched", text=response.text)

    def _get(self, url: str, *, resolved_ip: str) -> CrawlerHttpResponse:
        if self.transport is not None:
            with self._client() as client:
                response = client.get(url)
                return CrawlerHttpResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=response.content,
                )
        return get_via_resolved_ip(
            url=url,
            resolved_ip=resolved_ip,
            timeout_seconds=self.timeout_seconds,
            max_bytes=self.max_bytes,
            user_agent=self.user_agent,
        )

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": self.user_agent},
            transport=self.transport,
        )


class CrawlerHttpError(Exception):
    pass


class ResolvedHTTPConnection(http.client.HTTPConnection):
    def __init__(
        self,
        host: str,
        resolved_ip: str,
        *,
        port: int,
        timeout: float,
    ) -> None:
        super().__init__(host=host, port=port, timeout=timeout)
        self.resolved_ip = resolved_ip
        self.source_address_value: tuple[str, int] | None = None

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.resolved_ip, self.port),
            self.timeout,
            self.source_address_value,
        )


class ResolvedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        resolved_ip: str,
        *,
        port: int,
        timeout: float,
    ) -> None:
        self.ssl_context = ssl.create_default_context()
        super().__init__(host=host, port=port, timeout=timeout, context=self.ssl_context)
        self.resolved_ip = resolved_ip
        self.source_address_value: tuple[str, int] | None = None

    def connect(self) -> None:
        raw_sock = socket.create_connection(
            (self.resolved_ip, self.port),
            self.timeout,
            self.source_address_value,
        )
        self.sock = self.ssl_context.wrap_socket(raw_sock, server_hostname=self.host)


def get_via_resolved_ip(
    *,
    url: str,
    resolved_ip: str,
    timeout_seconds: float,
    max_bytes: int,
    user_agent: str,
) -> CrawlerHttpResponse:
    parsed = urlparse(url)
    if parsed.hostname is None:
        raise CrawlerHttpError("missing host")
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    connection: http.client.HTTPConnection
    if parsed.scheme == "https":
        connection = ResolvedHTTPSConnection(
            parsed.hostname,
            resolved_ip,
            port=port,
            timeout=timeout_seconds,
        )
    else:
        connection = ResolvedHTTPConnection(
            parsed.hostname,
            resolved_ip,
            port=port,
            timeout=timeout_seconds,
        )
    try:
        connection.request(
            "GET",
            path,
            headers={
                "Host": parsed.netloc,
                "User-Agent": user_agent,
                "Accept": "text/html, text/plain;q=0.8, */*;q=0.1",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        content = response.read(max_bytes + 1)
        return CrawlerHttpResponse(
            status_code=response.status,
            headers={key: value for key, value in response.getheaders()},
            content=content,
        )
    finally:
        connection.close()


def resolve_host_ips(host: str) -> list[str]:
    return list(
        {
            str(sockaddr[0])
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
