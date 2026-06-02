import pytest
from pydantic import ValidationError
from worker_app.crawler_parsers import (
    CrawlerParserRegistry,
    SourceParserBinding,
    parse_live_deal_html,
    parse_source_parsers,
)


def test_parser_extracts_minimum_live_deal_payload() -> None:
    raw_item = parse_live_deal_html(
        source_url="https://mock.example.com/deals/1",
        html="""
        <html>
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

    assert raw_item is not None
    assert raw_item.source_url == "https://mock.example.com/deals/1"
    assert raw_item.offer_type == "deal"
    assert raw_item.product_name == "Galaxy S26"
    assert raw_item.sale_price == 1_090_000
    assert raw_item.current_price is None


def test_parser_returns_none_when_required_fields_are_missing() -> None:
    assert (
        parse_live_deal_html(source_url="https://mock.example.com/deals/1", html="<html />")
        is None
    )


def test_source_parser_config_reads_host_to_parser_mapping() -> None:
    bindings = parse_source_parsers(
        "mock.example.com:dealmoa_article,other.example.com:dealmoa_article"
    )

    assert bindings == [
        SourceParserBinding(host="mock.example.com", parser_id="dealmoa_article"),
        SourceParserBinding(host="other.example.com", parser_id="dealmoa_article"),
    ]


def test_source_parser_config_rejects_invalid_entries() -> None:
    with pytest.raises(ValidationError):
        parse_source_parsers("missing-parser")


def test_parser_registry_uses_configured_parser_for_source_host() -> None:
    registry = CrawlerParserRegistry(
        [SourceParserBinding(host="mock.example.com", parser_id="dealmoa_article")]
    )

    raw_item, reason = registry.parse(
        source_url="https://mock.example.com/deals/1",
        html=dealmoa_article_html(),
    )

    assert reason is None
    assert raw_item is not None
    assert raw_item.source_url == "https://mock.example.com/deals/1"
    assert raw_item.product_name == "Galaxy S26"


def test_parser_registry_skips_unconfigured_source_host() -> None:
    registry = CrawlerParserRegistry(
        [SourceParserBinding(host="mock.example.com", parser_id="dealmoa_article")]
    )

    raw_item, reason = registry.parse(
        source_url="https://unknown.example.com/deals/1",
        html=dealmoa_article_html(),
    )

    assert raw_item is None
    assert reason == "parser_not_configured"


def test_parser_registry_skips_unsupported_parser_id() -> None:
    registry = CrawlerParserRegistry(
        [SourceParserBinding(host="mock.example.com", parser_id="unknown_parser")]
    )

    raw_item, reason = registry.parse(
        source_url="https://mock.example.com/deals/1",
        html=dealmoa_article_html(),
    )

    assert raw_item is None
    assert reason == "unsupported_source_parser"


def dealmoa_article_html() -> str:
    return """
    <article
      data-dealmoa-offer-type="deal"
      data-dealmoa-product-name="Galaxy S26"
      data-dealmoa-title="Galaxy S26 launch deal"
      data-dealmoa-sale-price="1090000"
      data-dealmoa-currency="KRW"
    ></article>
    """
