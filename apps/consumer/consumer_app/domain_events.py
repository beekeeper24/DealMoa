from typing import Any, Literal, TypedDict

from app.modules.products.repository import ProductRepository
from app.modules.search.use_cases import SearchClient, SearchUseCases

DomainEventType = Literal[
    "product.updated",
    "deal.created",
    "auction.created",
    "auction.bid.placed",
    "auction.favorite.created",
    "auction.favorite.deleted",
    "auction.view.recorded",
]

AUCTION_REFRESH_EVENT_TYPES = {
    "auction.created",
    "auction.bid.placed",
    "auction.favorite.created",
    "auction.favorite.deleted",
    "auction.view.recorded",
}


class DomainEventEnvelope(TypedDict):
    eventId: str
    eventType: str
    aggregateType: str
    aggregateId: str
    payload: dict[str, object]
    occurredAt: str


class DomainEventSearchIndexer:
    def __init__(
        self,
        *,
        product_repository: ProductRepository,
        search_client: SearchClient,
    ) -> None:
        self.product_repository = product_repository
        self.search_use_cases = SearchUseCases(product_repository, search_client)

    def handle(self, envelope: dict[str, Any]) -> bool:
        event_type = envelope.get("eventType")
        aggregate_id = envelope.get("aggregateId")
        if not isinstance(event_type, str) or not isinstance(aggregate_id, str):
            return False

        if event_type == "product.updated":
            product = self.product_repository.get_product(aggregate_id)
            if product is None:
                return False
            self.search_use_cases.index_product(product)
            return True

        if event_type == "deal.created":
            deal = self.product_repository.get_deal(aggregate_id)
            if deal is None:
                return False
            self.search_use_cases.index_deal(deal)
            return True

        if event_type in AUCTION_REFRESH_EVENT_TYPES:
            auction = self.product_repository.get_auction(aggregate_id)
            if auction is None:
                return False
            self.search_use_cases.index_auction(auction)
            return True

        return False
