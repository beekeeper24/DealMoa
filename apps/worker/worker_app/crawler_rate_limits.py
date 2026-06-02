from urllib.parse import urlparse


class CrawlerHostRunLimiter:
    def __init__(self, *, max_urls_per_host: int) -> None:
        self.max_urls_per_host = max_urls_per_host
        self.counts_by_host: dict[str, int] = {}

    def allow(self, source_url: str) -> bool:
        host = urlparse(source_url).netloc.casefold()
        current_count = self.counts_by_host.get(host, 0)
        if current_count >= self.max_urls_per_host:
            return False
        self.counts_by_host[host] = current_count + 1
        return True
