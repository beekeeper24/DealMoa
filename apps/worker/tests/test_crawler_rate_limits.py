from worker_app.crawler_rate_limits import CrawlerHostRunLimiter


def test_host_run_limiter_allows_up_to_configured_count_per_host() -> None:
    limiter = CrawlerHostRunLimiter(max_urls_per_host=2)

    assert limiter.allow("https://mock.example.com/deals/1") is True
    assert limiter.allow("https://mock.example.com/deals/2") is True
    assert limiter.allow("https://mock.example.com/deals/3") is False


def test_host_run_limiter_counts_hosts_independently_and_case_insensitively() -> None:
    limiter = CrawlerHostRunLimiter(max_urls_per_host=1)

    assert limiter.allow("https://MOCK.example.com/deals/1") is True
    assert limiter.allow("https://other.example.com/deals/1") is True
    assert limiter.allow("https://mock.example.com/deals/2") is False
