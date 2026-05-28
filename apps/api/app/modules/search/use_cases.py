from collections.abc import Sequence
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

    def list_auctions_for_search(self) -> Sequence[Auction]:
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


class SearchUseCases:
    def __init__(
        self,
        source_repository: SearchSourceRepository,
        search_client: SearchClient,
    ) -> None:
        self.source_repository = source_repository
        self.search_client = search_client

    def rebuild_indexes(self) -> dict[SearchIndexKind, int]:
        product_documents = [
            build_product_document(product)
            for product in self.source_repository.list_products_for_search()
        ]
        deal_documents = [
            build_deal_document(deal) for deal in self.source_repository.list_deals_for_search()
        ]
        auction_documents = [
            build_auction_document(auction)
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
        self.search_client.index_document("deals", build_deal_document(deal))

    def index_auction(self, auction: Auction) -> None:
        self.search_client.index_document("auctions", build_auction_document(auction))

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
