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
