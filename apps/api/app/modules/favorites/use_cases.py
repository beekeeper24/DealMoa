from collections.abc import Callable
from datetime import UTC, datetime

from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    ProductNotFoundException,
)
from app.core.pagination import CursorPage
from app.modules.favorites.models import AuctionFavorite, DealFavorite, ProductFavorite
from app.modules.favorites.repository import FavoritesRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


class FavoritesUseCases:
    def __init__(
        self,
        repository: FavoritesRepository,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository
        self.now = now

    def add_product_favorite(self, *, user_id: str, product_id: str) -> ProductFavorite:
        if self.repository.get_product(product_id) is None:
            raise ProductNotFoundException(product_id)
        existing = self.repository.get_product_favorite(user_id=user_id, product_id=product_id)
        if existing is not None:
            return existing
        now = self.now()
        return self.repository.create_product_favorite(
            ProductFavorite(user_id=user_id, product_id=product_id, created_at=now, updated_at=now)
        )

    def remove_product_favorite(self, *, user_id: str, product_id: str) -> None:
        if self.repository.get_product(product_id) is None:
            raise ProductNotFoundException(product_id)
        existing = self.repository.get_product_favorite(user_id=user_id, product_id=product_id)
        if existing is not None:
            self.repository.delete_product_favorite(existing)

    def list_product_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductFavorite]:
        return self.repository.list_product_favorites(user_id=user_id, limit=limit, cursor=cursor)

    def add_deal_favorite(self, *, user_id: str, deal_id: str) -> DealFavorite:
        if self.repository.get_deal(deal_id) is None:
            raise DealNotFoundException(deal_id)
        existing = self.repository.get_deal_favorite(user_id=user_id, deal_id=deal_id)
        if existing is not None:
            return existing
        now = self.now()
        return self.repository.create_deal_favorite(
            DealFavorite(user_id=user_id, deal_id=deal_id, created_at=now, updated_at=now)
        )

    def remove_deal_favorite(self, *, user_id: str, deal_id: str) -> None:
        if self.repository.get_deal(deal_id) is None:
            raise DealNotFoundException(deal_id)
        existing = self.repository.get_deal_favorite(user_id=user_id, deal_id=deal_id)
        if existing is not None:
            self.repository.delete_deal_favorite(existing)

    def list_deal_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[DealFavorite]:
        return self.repository.list_deal_favorites(user_id=user_id, limit=limit, cursor=cursor)

    def add_auction_favorite(self, *, user_id: str, auction_id: str) -> AuctionFavorite:
        if self.repository.get_auction(auction_id) is None:
            raise AuctionNotFoundException(auction_id)
        existing = self.repository.get_auction_favorite(user_id=user_id, auction_id=auction_id)
        if existing is not None:
            return existing
        now = self.now()
        return self.repository.create_auction_favorite(
            AuctionFavorite(user_id=user_id, auction_id=auction_id, created_at=now, updated_at=now)
        )

    def remove_auction_favorite(self, *, user_id: str, auction_id: str) -> None:
        if self.repository.get_auction(auction_id) is None:
            raise AuctionNotFoundException(auction_id)
        existing = self.repository.get_auction_favorite(user_id=user_id, auction_id=auction_id)
        if existing is not None:
            self.repository.delete_auction_favorite(existing)

    def list_auction_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[AuctionFavorite]:
        return self.repository.list_auction_favorites(user_id=user_id, limit=limit, cursor=cursor)
