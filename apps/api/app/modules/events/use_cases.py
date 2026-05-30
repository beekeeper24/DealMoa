from collections.abc import Callable
from datetime import UTC, datetime

from app.modules.events.models import DomainEvent
from app.modules.events.repository import DomainEventsRepository
from app.modules.favorites.models import AuctionFavorite
from app.modules.products.models import Auction, AuctionBid, AuctionView, Deal, Product


def utc_now() -> datetime:
    return datetime.now(UTC)


class DomainEventsUseCases:
    def __init__(
        self,
        *,
        repository: DomainEventsRepository,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository
        self.now = now

    def record_product_updated(self, product: Product) -> DomainEvent:
        return self._record_event(
            event_type="product.updated",
            aggregate_type="product",
            aggregate_id=product.id,
            payload={
                "productId": product.id,
                "name": product.name,
                "brand": product.brand,
                "modelName": product.model_name,
                "category": product.category,
                "specs": product.specs,
            },
        )

    def record_deal_created(self, deal: Deal) -> DomainEvent:
        return self._record_event(
            event_type="deal.created",
            aggregate_type="deal",
            aggregate_id=deal.id,
            payload={
                "dealId": deal.id,
                "productId": deal.product_id,
                "title": deal.title,
                "sourceUrl": deal.source_url,
                "seller": deal.seller,
                "originalPrice": deal.original_price,
                "salePrice": deal.sale_price,
                "currency": deal.currency,
                "status": deal.status,
            },
        )

    def record_deal_status_changed(
        self,
        *,
        deal: Deal,
        actor_user_id: str,
        previous_status: str,
        reason: str | None,
    ) -> DomainEvent:
        return self._record_event(
            event_type="deal.status.changed",
            aggregate_type="deal",
            aggregate_id=deal.id,
            payload={
                "dealId": deal.id,
                "productId": deal.product_id,
                "previousStatus": previous_status,
                "newStatus": deal.status,
                "actorUserId": actor_user_id,
                "reason": reason,
            },
        )

    def record_auction_created(self, auction: Auction) -> DomainEvent:
        return self._record_event(
            event_type="auction.created",
            aggregate_type="auction",
            aggregate_id=auction.id,
            payload={
                "auctionId": auction.id,
                "productId": auction.product_id,
                "title": auction.title,
                "sourceUrl": auction.source_url,
                "seller": auction.seller,
                "currentPrice": auction.current_price,
                "bidCount": auction.bid_count,
                "currency": auction.currency,
                "status": auction.status,
            },
        )

    def record_auction_status_changed(
        self,
        *,
        auction: Auction,
        actor_user_id: str,
        previous_status: str,
        reason: str | None,
    ) -> DomainEvent:
        return self._record_event(
            event_type="auction.status.changed",
            aggregate_type="auction",
            aggregate_id=auction.id,
            payload={
                "auctionId": auction.id,
                "productId": auction.product_id,
                "previousStatus": previous_status,
                "newStatus": auction.status,
                "actorUserId": actor_user_id,
                "reason": reason,
            },
        )

    def record_auction_bid_placed(
        self,
        *,
        auction: Auction,
        bid: AuctionBid,
        previous_highest_bidder_user_id: str | None = None,
    ) -> DomainEvent:
        return self._record_event(
            event_type="auction.bid.placed",
            aggregate_type="auction",
            aggregate_id=auction.id,
            payload={
                "auctionId": auction.id,
                "bidId": bid.id,
                "userId": bid.user_id,
                "amount": bid.amount,
                "currentPrice": auction.current_price,
                "bidCount": auction.bid_count,
                "currency": auction.currency,
                "previousHighestBidderUserId": previous_highest_bidder_user_id,
            },
        )

    def record_auction_favorite_created(self, favorite: AuctionFavorite) -> DomainEvent:
        return self._record_auction_favorite_event(
            event_type="auction.favorite.created",
            favorite=favorite,
        )

    def record_auction_favorite_deleted(self, favorite: AuctionFavorite) -> DomainEvent:
        return self._record_auction_favorite_event(
            event_type="auction.favorite.deleted",
            favorite=favorite,
        )

    def record_auction_view_recorded(self, view: AuctionView) -> DomainEvent:
        return self._record_event(
            event_type="auction.view.recorded",
            aggregate_type="auction",
            aggregate_id=view.auction_id,
            payload={
                "auctionId": view.auction_id,
                "viewId": view.id,
            },
        )

    def _record_event(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, object],
    ) -> DomainEvent:
        now = self.now()
        return self.repository.create_event(
            DomainEvent(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                payload_json=payload,
                created_at=now,
                updated_at=now,
            )
        )

    def _record_auction_favorite_event(
        self,
        *,
        event_type: str,
        favorite: AuctionFavorite,
    ) -> DomainEvent:
        return self._record_event(
            event_type=event_type,
            aggregate_type="auction",
            aggregate_id=favorite.auction_id,
            payload={
                "auctionId": favorite.auction_id,
                "favoriteId": favorite.id,
                "userId": favorite.user_id,
            },
        )
