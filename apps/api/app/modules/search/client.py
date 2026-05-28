import base64
import json
from typing import Any

import httpx

from app.core.exceptions import InvalidSearchCursorException, SearchUnavailableException
from app.core.pagination import CursorPage
from app.modules.search.documents import SearchDocument
from app.modules.search.indexes import SEARCH_INDEXES, SearchIndexKind

SEARCH_FIELDS: dict[SearchIndexKind, list[str]] = {
    "products": [
        "name^4",
        "name.autocomplete^2",
        "brand^3",
        "brand.autocomplete",
        "modelName^4",
        "modelName.autocomplete^2",
        "category",
        "specsText",
    ],
    "deals": [
        "title^4",
        "title.autocomplete^2",
        "seller",
        "seller.autocomplete",
    ],
    "auctions": [
        "title^4",
        "title.autocomplete^2",
        "seller",
        "seller.autocomplete",
    ],
}


def encode_search_cursor(sort_values: list[Any]) -> str:
    payload = json.dumps(sort_values, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_search_cursor(cursor: str) -> list[Any]:
    padding = "=" * (-len(cursor) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{cursor}{padding}".encode())
        values = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        raise InvalidSearchCursorException(cursor) from None
    if not isinstance(values, list):
        raise InvalidSearchCursorException(cursor)
    return values


class ElasticsearchSearchClient:
    def __init__(
        self,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    def recreate_indexes(self) -> None:
        try:
            with self._client(timeout=30.0) as client:
                for spec in SEARCH_INDEXES.values():
                    delete_response = client.delete(f"/{spec.index_name}")
                    if delete_response.status_code not in {200, 404}:
                        delete_response.raise_for_status()
                    body = {**spec.body, "aliases": {spec.alias_name: {}}}
                    client.put(f"/{spec.index_name}", json=body).raise_for_status()
        except httpx.HTTPError:
            raise SearchUnavailableException() from None

    def replace_documents(
        self,
        kind: SearchIndexKind,
        documents: list[SearchDocument],
    ) -> None:
        spec = SEARCH_INDEXES[kind]
        if not documents:
            self._refresh(spec.alias_name)
            return

        lines: list[str] = []
        for document in documents:
            lines.append(json.dumps({"index": {"_index": spec.alias_name, "_id": document["id"]}}))
            lines.append(json.dumps(document, ensure_ascii=False))
        payload = "\n".join(lines) + "\n"

        try:
            with self._client(timeout=30.0) as client:
                response = client.post(
                    "/_bulk",
                    content=payload,
                    headers={"Content-Type": "application/x-ndjson"},
                    params={"refresh": "true"},
                )
                response.raise_for_status()
                body = response.json()
                if body.get("errors") is True:
                    raise SearchUnavailableException()
        except httpx.HTTPError:
            raise SearchUnavailableException() from None

    def index_document(self, kind: SearchIndexKind, document: SearchDocument) -> None:
        spec = SEARCH_INDEXES[kind]
        try:
            with self._client(timeout=10.0) as client:
                response = client.put(
                    f"/{spec.alias_name}/_doc/{document['id']}",
                    content=json.dumps(document, ensure_ascii=False, separators=(",", ":")),
                    headers={"Content-Type": "application/json"},
                    params={"refresh": "true"},
                )
                response.raise_for_status()
        except httpx.HTTPError:
            raise SearchUnavailableException() from None

    def search(
        self,
        kind: SearchIndexKind,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        spec = SEARCH_INDEXES[kind]
        body: dict[str, Any] = {
            "size": limit + 1,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": SEARCH_FIELDS[kind],
                    "type": "best_fields",
                    "operator": "and",
                }
            },
            "sort": [
                {"_score": "desc"},
                {"createdAt": "desc"},
                {"id": "desc"},
            ],
        }
        if cursor is not None:
            body["search_after"] = decode_search_cursor(cursor)

        try:
            with self._client(timeout=10.0) as client:
                response = client.post(f"/{spec.alias_name}/_search", json=body)
                response.raise_for_status()
                hits = response.json()["hits"]["hits"]
        except httpx.HTTPError:
            raise SearchUnavailableException() from None

        page_hits = hits[:limit]
        items = [self._search_item(hit) for hit in page_hits]
        next_cursor = None
        if len(hits) > limit and page_hits:
            next_cursor = encode_search_cursor(page_hits[-1]["sort"])
        return CursorPage(items=items, next_cursor=next_cursor)

    def _refresh(self, alias_name: str) -> None:
        try:
            with self._client(timeout=10.0) as client:
                client.post(f"/{alias_name}/_refresh").raise_for_status()
        except httpx.HTTPError:
            raise SearchUnavailableException() from None

    def _search_item(self, hit: dict[str, Any]) -> dict[str, Any]:
        source = dict(hit["_source"])
        source["score"] = hit["_score"]
        return source

    def _client(self, *, timeout: float) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=self.transport,
        )
