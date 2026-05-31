from datetime import UTC, datetime
from typing import Any

from app.core.pagination import CursorPage
from app.modules.products.models import Auction, Deal, Product
from app.modules.search.indexes import SearchIndexKind
from app.modules.search.use_cases import SearchUseCases


class FakeSearchSourceRepository:
    def list_products_for_search(self) -> list[Product]:
        return [
            Product(
                id="product-1",
                name="Galaxy S26",
                brand="Samsung",
                model_name="SM-S260",
                category="smartphone",
                specs=None,
                created_at=datetime(2026, 5, 25, tzinfo=UTC),
                updated_at=datetime(2026, 5, 25, tzinfo=UTC),
            )
        ]

    def list_deals_for_search(self) -> list[Deal]:
        return [
            Deal(
                id="deal-1",
                product_id="product-1",
                title="Galaxy S26 launch deal",
                source_url="https://example.com/deals/galaxy-s26",
                seller=None,
                original_price=None,
                sale_price=1090000,
                currency="KRW",
                status="active",
                started_at=None,
                ended_at=None,
                created_at=datetime(2026, 5, 25, tzinfo=UTC),
                updated_at=datetime(2026, 5, 25, tzinfo=UTC),
            )
        ]

    def list_deal_favorite_counts(self) -> dict[str, int]:
        return {"deal-1": 9}

    def count_deal_favorites(self, deal_id: str) -> int:
        return {"deal-1": 9}.get(deal_id, 0)

    def list_auctions_for_search(self) -> list[Auction]:
        return [
            Auction(
                id="auction-1",
                product_id="product-1",
                title="Galaxy S26 sealed auction",
                source_url="https://example.com/auctions/galaxy-s26",
                seller=None,
                current_price=720000,
                bid_count=3,
                currency="KRW",
                status="active",
                ends_at=None,
                created_at=datetime(2026, 5, 25, tzinfo=UTC),
                updated_at=datetime(2026, 5, 25, tzinfo=UTC),
            )
        ]

    def list_auction_favorite_counts(self) -> dict[str, int]:
        return {"auction-1": 7}

    def list_auction_view_counts_since(self, since: datetime) -> dict[str, int]:
        return {"auction-1": 11}

    def count_auction_favorites(self, auction_id: str) -> int:
        return {"auction-1": 7}.get(auction_id, 0)

    def count_auction_views_since(self, auction_id: str, since: datetime) -> int:
        return {"auction-1": 11}.get(auction_id, 0)


class RecordingSearchClient:
    def __init__(self) -> None:
        self.recreated = False
        self.replaced: list[tuple[SearchIndexKind, list[dict[str, Any]]]] = []
        self.indexed: list[tuple[SearchIndexKind, dict[str, Any]]] = []

    def recreate_indexes(self) -> None:
        self.recreated = True

    def replace_documents(
        self,
        kind: SearchIndexKind,
        documents: list[dict[str, Any]],
    ) -> None:
        self.replaced.append((kind, documents))

    def index_document(self, kind: SearchIndexKind, document: dict[str, Any]) -> None:
        self.indexed.append((kind, document))

    def search(
        self,
        kind: SearchIndexKind,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("rebuild test should not call search")

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("rebuild test should not call auction ranking")

    def rank_deals(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("rebuild test should not call deal ranking")


def test_rebuild_indexes_recreates_indexes_and_replaces_all_documents() -> None:
    search_client = RecordingSearchClient()
    use_cases = SearchUseCases(FakeSearchSourceRepository(), search_client)

    summary = use_cases.rebuild_indexes()

    assert search_client.recreated is True
    assert [kind for kind, _documents in search_client.replaced] == [
        "products",
        "deals",
        "auctions",
    ]
    assert search_client.replaced[0][1][0]["id"] == "product-1"
    assert search_client.replaced[1][1][0]["id"] == "deal-1"
    assert search_client.replaced[1][1][0]["trustScore"] == 10
    assert search_client.replaced[1][1][0]["favoriteCount"] == 9
    assert search_client.replaced[2][1][0]["id"] == "auction-1"
    assert search_client.replaced[2][1][0]["favoriteCount"] == 7
    assert search_client.replaced[2][1][0]["viewMomentum"] == 11
    assert search_client.replaced[2][1][0]["trustScore"] == 5
    assert summary == {"products": 1, "deals": 1, "auctions": 1}


def test_index_single_product_deal_and_auction_documents() -> None:
    search_client = RecordingSearchClient()
    source_repository = FakeSearchSourceRepository()
    use_cases = SearchUseCases(source_repository, search_client)

    use_cases.index_product(source_repository.list_products_for_search()[0])
    use_cases.index_deal(source_repository.list_deals_for_search()[0])
    use_cases.index_auction(source_repository.list_auctions_for_search()[0])

    assert [kind for kind, _document in search_client.indexed] == [
        "products",
        "deals",
        "auctions",
    ]
    assert search_client.indexed[0][1]["id"] == "product-1"
    assert search_client.indexed[1][1]["id"] == "deal-1"
    assert search_client.indexed[1][1]["trustScore"] == 10
    assert search_client.indexed[1][1]["favoriteCount"] == 9
    assert search_client.indexed[2][1]["id"] == "auction-1"
    assert search_client.indexed[2][1]["favoriteCount"] == 7
    assert search_client.indexed[2][1]["viewMomentum"] == 11
    assert search_client.indexed[2][1]["trustScore"] == 5
