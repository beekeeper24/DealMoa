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
