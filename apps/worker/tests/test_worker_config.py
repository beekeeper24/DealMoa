from pytest import MonkeyPatch
from worker_app.config import WorkerSettings


def test_live_crawler_settings_default_to_no_external_fetch(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CRAWLER_LIVE_URLS", "")
    monkeypatch.setenv("CRAWLER_SOURCE_PARSERS", "mock.example.com:dealmoa_article")
    monkeypatch.setenv("CRAWLER_HTTP_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("CRAWLER_HTTP_MAX_BYTES", "1048576")
    monkeypatch.setenv("CRAWLER_USER_AGENT", "DealMoaBot/0.1 (+https://dealmoa.local/crawler)")
    settings = WorkerSettings()

    assert settings.crawler_live_urls == ""
    assert settings.crawler_source_parsers == "mock.example.com:dealmoa_article"
    assert settings.crawler_http_timeout_seconds == 5.0
    assert settings.crawler_http_max_bytes == 1_048_576
    assert settings.crawler_user_agent == "DealMoaBot/0.1 (+https://dealmoa.local/crawler)"
