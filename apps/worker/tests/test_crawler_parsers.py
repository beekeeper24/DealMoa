from worker_app.crawler_parsers import parse_live_deal_html


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
