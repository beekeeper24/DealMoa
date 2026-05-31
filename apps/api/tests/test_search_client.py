from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from app.core.exceptions import InvalidSearchCursorException, SearchUnavailableException
from app.modules.search.client import (
    ElasticsearchSearchClient,
    decode_search_cursor,
    encode_search_cursor,
)


def test_search_cursor_round_trips_sort_values() -> None:
    cursor = encode_search_cursor([12.5, "2026-05-25T00:00:00Z", "product-1"])

    assert decode_search_cursor(cursor) == [12.5, "2026-05-25T00:00:00Z", "product-1"]


def test_invalid_search_cursor_raises_domain_exception() -> None:
    with pytest.raises(InvalidSearchCursorException) as exc_info:
        decode_search_cursor("not-valid-base64")

    assert exc_info.value.error_code.code == "INVALID_SEARCH_CURSOR"
    assert exc_info.value.details == {"cursor": "not-valid-base64"}


def test_search_backend_http_error_raises_search_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SearchUnavailableException):
        client.search("products", query="galaxy", limit=20, cursor=None)


def test_bulk_indexing_errors_raise_search_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": True, "items": []})

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SearchUnavailableException):
        client.replace_documents("products", [{"id": "product-1", "name": "Galaxy"}])


def test_offer_search_filters_to_active_status() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"hits": {"hits": []}})

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    client.search("deals", query="galaxy", limit=20, cursor=None)
    client.search("auctions", query="galaxy", limit=20, cursor=None)

    deal_body = json_from_request(requests[0])
    auction_body = json_from_request(requests[1])
    assert deal_body["query"]["bool"]["filter"] == [{"term": {"status": "active"}}]
    assert auction_body["query"]["bool"]["filter"] == [{"term": {"status": "active"}}]
    assert deal_body["query"]["bool"]["must"]["multi_match"]["query"] == "galaxy"
    assert auction_body["query"]["bool"]["must"]["multi_match"]["query"] == "galaxy"


def test_index_document_puts_document_to_alias_with_refresh() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"result": "updated"})

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    client.index_document("products", {"id": "product-1", "name": "Galaxy S26"})

    assert len(requests) == 1
    assert requests[0].method == "PUT"
    assert requests[0].url.path == "/products_current/_doc/product-1"
    assert requests[0].url.params["refresh"] == "true"
    assert requests[0].read() == b'{"id":"product-1","name":"Galaxy S26"}'


def test_rank_auctions_uses_activity_script_over_active_auctions() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_score": 52.0,
                            "_source": {
                                "id": "auction-1",
                                "productId": "product-1",
                                "title": "Galaxy S26 sealed auction",
                                "sourceUrl": "https://example.com/auctions/galaxy-s26",
                                "seller": "Auction House",
                                "currentPrice": 780000,
                                "bidCount": 5,
                                "uniqueBidderCount": 3,
                                "favoriteCount": 7,
                                "viewMomentum": 9,
                                "trustScore": 5,
                                "currency": "KRW",
                                "status": "active",
                                "endsAt": "2026-05-29T12:00:00Z",
                                "createdAt": "2026-05-29T00:00:00Z",
                                "updatedAt": "2026-05-29T09:00:00Z",
                            },
                            "sort": [52.0, "2026-05-29T09:00:00Z", "auction-1"],
                        }
                    ]
                }
            },
        )

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    page = client.rank_auctions(
        limit=1,
        cursor=None,
        now=datetime(2026, 5, 29, 9, 0, tzinfo=UTC),
    )

    body = json_from_request(requests[0])
    script = body["query"]["script_score"]["script"]
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/auctions_current/_search"
    assert body["size"] == 2
    assert body["query"]["script_score"]["query"] == {"term": {"status": "active"}}
    assert "bidCount" in script["source"]
    assert "uniqueBidderCount" in script["source"]
    assert "favoriteCount" in script["source"]
    assert "viewMomentum" in script["source"]
    assert "trustScore" in script["source"]
    assert "endsAt" in script["source"]
    assert script["params"]["bidActivityWeight"] == 45.0
    assert script["params"]["uniqueBidderWeight"] == 20.0
    assert script["params"]["favoriteCountWeight"] == 10.0
    assert script["params"]["viewMomentumWeight"] == 15.0
    assert script["params"]["trustScoreWeight"] == 5.0
    assert script["params"]["endingSoonWeight"] == 5.0
    assert body["sort"] == [{"_score": "desc"}, {"updatedAt": "desc"}, {"id": "desc"}]
    assert page.items[0]["score"] == 52.0


def test_rank_deals_uses_hot_deal_score_script_over_active_deals() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_score": 78.0,
                            "_source": {
                                "id": "deal-1",
                                "productId": "product-1",
                                "title": "Galaxy S26 launch deal",
                                "sourceUrl": "https://example.com/deals/galaxy-s26",
                                "seller": "Example Store",
                                "originalPrice": 1400000,
                                "salePrice": 1090000,
                                "favoriteCount": 9,
                                "trustScore": 10,
                                "currency": "KRW",
                                "status": "active",
                                "startedAt": "2026-05-29T00:00:00Z",
                                "endedAt": None,
                                "createdAt": "2026-05-29T00:00:00Z",
                                "updatedAt": "2026-05-29T09:00:00Z",
                            },
                            "sort": [78.0, "2026-05-29T09:00:00Z", "deal-1"],
                        }
                    ]
                }
            },
        )

    client = ElasticsearchSearchClient(
        "http://elasticsearch.test",
        transport=httpx.MockTransport(handler),
    )

    page = client.rank_deals(
        limit=1,
        cursor=None,
        now=datetime(2026, 5, 29, 9, 0, tzinfo=UTC),
    )

    body = json_from_request(requests[0])
    script = body["query"]["script_score"]["script"]
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/deals_current/_search"
    assert body["size"] == 2
    assert body["query"]["script_score"]["query"] == {"term": {"status": "active"}}
    assert "originalPrice" in script["source"]
    assert "salePrice" in script["source"]
    assert "favoriteCount" in script["source"]
    assert "createdAt" in script["source"]
    assert "trustScore" in script["source"]
    assert script["params"]["priceScoreWeight"] == 50.0
    assert script["params"]["favoriteCountWeight"] == 30.0
    assert script["params"]["freshnessWeight"] == 10.0
    assert script["params"]["trustScoreWeight"] == 10.0
    assert body["sort"] == [{"_score": "desc"}, {"updatedAt": "desc"}, {"id": "desc"}]
    assert page.items[0]["score"] == 78.0


def json_from_request(request: httpx.Request) -> dict[str, Any]:
    import json

    body = request.read()
    parsed = json.loads(body)
    assert isinstance(parsed, dict)
    return parsed
