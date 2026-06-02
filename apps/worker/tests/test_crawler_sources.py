import pytest
from pydantic import ValidationError
from worker_app.crawler_sources import (
    CrawlerRawItem,
    CrawlerSourceProfile,
    CrawlerSourceRegistry,
    parse_source_profiles,
)


def test_source_profile_parser_reads_allowlisted_and_blocked_sources() -> None:
    profiles = parse_source_profiles(
        "mock.example.com:trusted:allow,blocked.example.com:low:block"
    )

    assert profiles == [
        CrawlerSourceProfile(host="mock.example.com", reputation="trusted", action="allow"),
        CrawlerSourceProfile(host="blocked.example.com", reputation="low", action="block"),
    ]


def test_source_profile_parser_rejects_invalid_entries() -> None:
    with pytest.raises(ValidationError):
        parse_source_profiles("missing-action:trusted")


def test_registry_skips_unknown_and_blocked_source_hosts() -> None:
    registry = CrawlerSourceRegistry(
        [
            CrawlerSourceProfile(host="mock.example.com", reputation="trusted", action="allow"),
            CrawlerSourceProfile(host="blocked.example.com", reputation="low", action="block"),
        ]
    )

    assert registry.parse(raw_item(source_url="https://unknown.example.com/deals/1")) is None
    assert registry.parse(raw_item(source_url="https://blocked.example.com/deals/1")) is None


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


def test_registry_parses_allowed_item_into_submission_payload() -> None:
    registry = CrawlerSourceRegistry(
        [CrawlerSourceProfile(host="mock.example.com", reputation="trusted", action="allow")]
    )

    parsed = registry.parse(raw_item())

    assert parsed is not None
    assert parsed["sourceUrl"] == "https://mock.example.com/deals/1"
    assert parsed["offerType"] == "deal"
    assert parsed["salePrice"] == 1090000
    assert parsed["description"] == "Crawler source reputation: trusted"


def raw_item(source_url: str = "https://mock.example.com/deals/1") -> CrawlerRawItem:
    return CrawlerRawItem(
        offerType="deal",
        sourceUrl=source_url,
        productName="Galaxy S26",
        brand="Samsung",
        modelName="SM-S260",
        category="smartphone",
        title="Galaxy S26 launch deal",
        seller="Mock Hotdeal",
        originalPrice=1400000,
        salePrice=1090000,
        currentPrice=None,
        currency="KRW",
    )
