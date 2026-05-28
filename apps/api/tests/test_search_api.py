from typing import Any

from app.core.pagination import CursorPage
from app.main import create_app
from app.modules.search.router import get_search_use_cases
from fastapi.testclient import TestClient


class FakeSearchUseCases:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int, str | None] | tuple[str, int, str | None]] = []

    def search_products(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("products", query, limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "product-1",
                    "name": "Galaxy S26",
                    "brand": "Samsung",
                    "modelName": "SM-S260",
                    "category": "smartphone",
                    "specsText": "storage 256GB",
                    "createdAt": "2026-05-25T00:00:00Z",
                    "updatedAt": "2026-05-25T00:00:00Z",
                    "score": 12.5,
                }
            ],
            next_cursor="cursor-2",
        )

    def search_deals(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("deals", query, limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "deal-1",
                    "productId": "product-1",
                    "title": "Galaxy S26 launch deal",
                    "sourceUrl": "https://example.com/deals/galaxy-s26",
                    "seller": "Example Store",
                    "originalPrice": None,
                    "salePrice": 1090000,
                    "currency": "KRW",
                    "status": "active",
                    "startedAt": None,
                    "endedAt": None,
                    "createdAt": "2026-05-25T00:00:00Z",
                    "updatedAt": "2026-05-25T00:00:00Z",
                    "score": 9.0,
                }
            ],
            next_cursor=None,
        )

    def search_auctions(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("auctions", query, limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "auction-1",
                    "productId": "product-1",
                    "title": "Galaxy S26 sealed auction",
                    "sourceUrl": "https://example.com/auctions/galaxy-s26",
                    "seller": "Auction House",
                    "currentPrice": 720000,
                    "bidCount": 3,
                    "uniqueBidderCount": 2,
                    "currency": "KRW",
                    "status": "active",
                    "endsAt": None,
                    "createdAt": "2026-05-25T00:00:00Z",
                    "updatedAt": "2026-05-25T00:00:00Z",
                    "score": 8.5,
                }
            ],
            next_cursor=None,
        )

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        self.calls.append(("auction_activity", limit, cursor))
        return CursorPage(
            items=[
                {
                    "id": "auction-1",
                    "productId": "product-1",
                    "title": "Galaxy S26 sealed auction",
                    "sourceUrl": "https://example.com/auctions/galaxy-s26",
                    "seller": "Auction House",
                    "currentPrice": 720000,
                    "bidCount": 3,
                    "uniqueBidderCount": 2,
                    "currency": "KRW",
                    "status": "active",
                    "endsAt": None,
                    "createdAt": "2026-05-25T00:00:00Z",
                    "updatedAt": "2026-05-25T00:00:00Z",
                    "score": 41.0,
                }
            ],
            next_cursor="activity-cursor-2",
        )

    def rebuild_indexes(self) -> dict[str, int]:
        return {"products": 1, "deals": 1, "auctions": 1}


def make_search_test_client(use_cases: FakeSearchUseCases) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_search_use_cases] = lambda: use_cases
    return TestClient(app)


def test_search_products_returns_items_and_next_cursor() -> None:
    use_cases = FakeSearchUseCases()
    client = make_search_test_client(use_cases)

    response = client.get("/api/v1/search/products?q=galaxy&limit=1")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "product-1"
    assert response.json()["items"][0]["score"] == 12.5
    assert response.json()["nextCursor"] == "cursor-2"
    assert use_cases.calls == [("products", "galaxy", 1, None)]


def test_search_deals_passes_cursor_to_use_case() -> None:
    use_cases = FakeSearchUseCases()
    client = make_search_test_client(use_cases)

    response = client.get("/api/v1/search/deals?q=galaxy&cursor=cursor-1")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "deal-1"
    assert use_cases.calls == [("deals", "galaxy", 20, "cursor-1")]


def test_search_auctions_returns_activity_fields() -> None:
    use_cases = FakeSearchUseCases()
    client = make_search_test_client(use_cases)

    response = client.get("/api/v1/search/auctions?q=galaxy")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "auction-1"
    assert response.json()["items"][0]["bidCount"] == 3
    assert response.json()["items"][0]["uniqueBidderCount"] == 2
    assert use_cases.calls == [("auctions", "galaxy", 20, None)]


def test_rank_auctions_by_activity_calls_ranking_use_case() -> None:
    use_cases = FakeSearchUseCases()
    client = make_search_test_client(use_cases)

    response = client.get("/api/v1/search/auctions/activity?limit=1")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "auction-1"
    assert response.json()["items"][0]["score"] == 41.0
    assert response.json()["nextCursor"] == "activity-cursor-2"
    assert use_cases.calls == [("auction_activity", 1, None)]


def test_rebuild_search_indexes_returns_counts() -> None:
    client = make_search_test_client(FakeSearchUseCases())

    response = client.post("/api/v1/admin/search/reindex")

    assert response.status_code == 200
    assert response.json() == {"products": 1, "deals": 1, "auctions": 1}


def test_search_query_validation_uses_common_error_shape() -> None:
    client = make_search_test_client(FakeSearchUseCases())

    response = client.get("/api/v1/search/products?q=")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
