from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from app.core.pagination import CursorPage
from app.modules.products.models import Auction, Deal, Product
from app.modules.search.documents import (
    SearchDocument,
    build_auction_document,
    build_deal_document,
    build_product_document,
)
from app.modules.search.indexes import SearchIndexKind


class SearchSourceRepository(Protocol):
    def list_products_for_search(self) -> Sequence[Product]:
        pass

    def list_deals_for_search(self) -> Sequence[Deal]:
        pass

    def list_deal_favorite_counts(self) -> dict[str, int]:
        pass

    def count_deal_favorites(self, deal_id: str) -> int:
        pass

    def list_auctions_for_search(self) -> Sequence[Auction]:
        pass

    def list_auction_favorite_counts(self) -> dict[str, int]:
        pass

    def list_auction_view_counts_since(self, since: datetime) -> dict[str, int]:
        pass

    def count_auction_favorites(self, auction_id: str) -> int:
        pass

    def count_auction_views_since(self, auction_id: str, since: datetime) -> int:
        pass


class SearchClient(Protocol):
    def recreate_indexes(self) -> None:
        pass

    def replace_documents(
        self,
        kind: SearchIndexKind,
        documents: list[SearchDocument],
    ) -> None:
        pass

    def index_document(self, kind: SearchIndexKind, document: SearchDocument) -> None:
        pass

    def search(
        self,
        kind: SearchIndexKind,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass

    def rank_deals(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        pass


class SearchUseCases:
    def __init__(
        self,
        source_repository: SearchSourceRepository,
        search_client: SearchClient,
        now: Callable[[], datetime] | None = None,
        view_momentum_window: timedelta = timedelta(hours=24),
    ) -> None:
        self.source_repository = source_repository
        self.search_client = search_client
        self.now = now or utc_now
        self.view_momentum_window = view_momentum_window

    def rebuild_indexes(self) -> dict[SearchIndexKind, int]:
        product_documents = [
            build_product_document(product)
            for product in self.source_repository.list_products_for_search()
        ]
        deal_favorite_counts = self.source_repository.list_deal_favorite_counts()
        deal_documents = [
            build_deal_document(deal, favorite_count=deal_favorite_counts.get(deal.id, 0))
            for deal in self.source_repository.list_deals_for_search()
        ]
        auction_favorite_counts = self.source_repository.list_auction_favorite_counts()
        auction_view_counts = self.source_repository.list_auction_view_counts_since(
            self._view_momentum_since()
        )
        auction_documents = [
            build_auction_document(
                auction,
                favorite_count=auction_favorite_counts.get(auction.id, 0),
                view_momentum=auction_view_counts.get(auction.id, 0),
            )
            for auction in self.source_repository.list_auctions_for_search()
        ]

        self.search_client.recreate_indexes()
        self.search_client.replace_documents("products", product_documents)
        self.search_client.replace_documents("deals", deal_documents)
        self.search_client.replace_documents("auctions", auction_documents)

        return {
            "products": len(product_documents),
            "deals": len(deal_documents),
            "auctions": len(auction_documents),
        }

    def index_product(self, product: Product) -> None:
        self.search_client.index_document("products", build_product_document(product))

    def index_deal(self, deal: Deal) -> None:
        self.search_client.index_document(
            "deals",
            build_deal_document(
                deal,
                favorite_count=self.source_repository.count_deal_favorites(deal.id),
            ),
        )

    def index_auction(self, auction: Auction) -> None:
        self.search_client.index_document(
            "auctions",
            build_auction_document(
                auction,
                favorite_count=self.source_repository.count_auction_favorites(auction.id),
                view_momentum=self.source_repository.count_auction_views_since(
                    auction.id,
                    self._view_momentum_since(),
                ),
            ),
        )

    def search_products(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        return self.search_client.search("products", query=query, limit=limit, cursor=cursor)

    def search_deals(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        return self.search_client.search("deals", query=query, limit=limit, cursor=cursor)

    def search_auctions(
        self,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        return self.search_client.search("auctions", query=query, limit=limit, cursor=cursor)

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        return self.search_client.rank_auctions(limit=limit, cursor=cursor)

    def rank_deals(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        return self.search_client.rank_deals(limit=limit, cursor=cursor)

    def _view_momentum_since(self) -> datetime:
        return self.now() - self.view_momentum_window


def utc_now() -> datetime:
    return datetime.now(UTC)
