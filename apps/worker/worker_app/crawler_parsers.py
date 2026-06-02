from html.parser import HTMLParser
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from worker_app.crawler_sources import CrawlerRawItem

SUPPORTED_PARSER_IDS = {"dealmoa_article"}


class SourceParserBinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str = Field(min_length=1)
    parser_id: str = Field(min_length=1)


class CrawlerParserRegistry:
    def __init__(self, bindings: list[SourceParserBinding]) -> None:
        self.parser_by_host = {binding.host.casefold(): binding.parser_id for binding in bindings}

    def parse(self, *, source_url: str, html: str) -> tuple[CrawlerRawItem | None, str | None]:
        host = urlparse(source_url).netloc.casefold()
        parser_id = self.parser_by_host.get(host)
        if parser_id is None:
            return None, "parser_not_configured"
        if parser_id not in SUPPORTED_PARSER_IDS:
            return None, "unsupported_source_parser"
        raw_item = parse_live_deal_html(source_url=source_url, html=html)
        if raw_item is None:
            return None, "parse_failed"
        return raw_item, None


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


def parse_source_parsers(value: str) -> list[SourceParserBinding]:
    bindings: list[SourceParserBinding] = []
    for raw_entry in [entry.strip() for entry in value.split(",") if entry.strip()]:
        parts = [part.strip() for part in raw_entry.split(":")]
        if len(parts) != 2:
            raise ValidationError.from_exception_data(
                "SourceParserBinding",
                [
                    {
                        "type": "value_error",
                        "loc": ("sourceParser",),
                        "input": raw_entry,
                        "ctx": {"error": ValueError("expected host:parser_id")},
                    }
                ],
            )
        bindings.append(SourceParserBinding(host=parts[0], parser_id=parts[1]))
    return bindings
