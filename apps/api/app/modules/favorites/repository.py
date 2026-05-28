from typing import TypeVar

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.favorites.models import AuctionFavorite, DealFavorite, ProductFavorite
from app.modules.products.models import Auction, Deal, Product

FavoriteT = TypeVar("FavoriteT", ProductFavorite, DealFavorite, AuctionFavorite)


class FavoritesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_product(self, product_id: str) -> Product | None:
        return self.session.get(Product, product_id)

    def get_deal(self, deal_id: str) -> Deal | None:
        return self.session.get(Deal, deal_id)

    def get_auction(self, auction_id: str) -> Auction | None:
        return self.session.get(Auction, auction_id)

    def get_product_favorite(self, *, user_id: str, product_id: str) -> ProductFavorite | None:
        statement = select(ProductFavorite).where(
            ProductFavorite.user_id == user_id,
            ProductFavorite.product_id == product_id,
        )
        return self.session.scalar(statement)

    def create_product_favorite(self, favorite: ProductFavorite) -> ProductFavorite:
        self.session.add(favorite)
        self.session.flush()
        return favorite

    def list_product_favorite_user_ids(self, product_id: str) -> list[str]:
        statement = (
            select(ProductFavorite.user_id)
            .where(ProductFavorite.product_id == product_id)
            .order_by(ProductFavorite.user_id)
        )
        return list(self.session.scalars(statement))

    def delete_product_favorite(self, favorite: ProductFavorite) -> None:
        self.session.delete(favorite)
        self.session.flush()

    def list_product_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductFavorite]:
        statement = (
            select(ProductFavorite)
            .where(ProductFavorite.user_id == user_id)
            .order_by(ProductFavorite.created_at.desc(), ProductFavorite.id.desc())
        )
        if cursor is not None:
            cursor_favorite = self.session.get(ProductFavorite, cursor)
            if cursor_favorite is None or cursor_favorite.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, ProductFavorite, cursor_favorite)
        return self._page(statement, limit)

    def get_deal_favorite(self, *, user_id: str, deal_id: str) -> DealFavorite | None:
        statement = select(DealFavorite).where(
            DealFavorite.user_id == user_id,
            DealFavorite.deal_id == deal_id,
        )
        return self.session.scalar(statement)

    def create_deal_favorite(self, favorite: DealFavorite) -> DealFavorite:
        self.session.add(favorite)
        self.session.flush()
        return favorite

    def delete_deal_favorite(self, favorite: DealFavorite) -> None:
        self.session.delete(favorite)
        self.session.flush()

    def list_deal_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[DealFavorite]:
        statement = (
            select(DealFavorite)
            .where(DealFavorite.user_id == user_id)
            .order_by(DealFavorite.created_at.desc(), DealFavorite.id.desc())
        )
        if cursor is not None:
            cursor_favorite = self.session.get(DealFavorite, cursor)
            if cursor_favorite is None or cursor_favorite.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, DealFavorite, cursor_favorite)
        return self._page(statement, limit)

    def get_auction_favorite(self, *, user_id: str, auction_id: str) -> AuctionFavorite | None:
        statement = select(AuctionFavorite).where(
            AuctionFavorite.user_id == user_id,
            AuctionFavorite.auction_id == auction_id,
        )
        return self.session.scalar(statement)

    def create_auction_favorite(self, favorite: AuctionFavorite) -> AuctionFavorite:
        self.session.add(favorite)
        self.session.flush()
        return favorite

    def delete_auction_favorite(self, favorite: AuctionFavorite) -> None:
        self.session.delete(favorite)
        self.session.flush()

    def list_auction_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[AuctionFavorite]:
        statement = (
            select(AuctionFavorite)
            .where(AuctionFavorite.user_id == user_id)
            .order_by(AuctionFavorite.created_at.desc(), AuctionFavorite.id.desc())
        )
        if cursor is not None:
            cursor_favorite = self.session.get(AuctionFavorite, cursor)
            if cursor_favorite is None or cursor_favorite.user_id != user_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, AuctionFavorite, cursor_favorite)
        return self._page(statement, limit)

    def _page(self, statement: Select[tuple[FavoriteT]], limit: int) -> CursorPage[FavoriteT]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[FavoriteT]],
        model: type[FavoriteT],
        cursor_item: FavoriteT,
    ) -> Select[tuple[FavoriteT]]:
        return statement.where(
            or_(
                model.created_at < cursor_item.created_at,
                and_(model.created_at == cursor_item.created_at, model.id < cursor_item.id),
            )
        )
