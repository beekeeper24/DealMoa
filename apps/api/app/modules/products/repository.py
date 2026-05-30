from datetime import datetime
from typing import TypeVar

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import InvalidSearchCursorException
from app.core.pagination import CursorPage
from app.modules.favorites.models import AuctionFavorite
from app.modules.products.models import Auction, AuctionBid, Deal, Product

T = TypeVar("T", Product, Deal, Auction)


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_product(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product

    def get_product(self, product_id: str) -> Product | None:
        return self.session.get(Product, product_id)

    def list_products(self, *, limit: int, cursor: str | None) -> CursorPage[Product]:
        statement = select(Product).order_by(Product.created_at.desc(), Product.id.desc())
        if cursor is not None:
            cursor_product = self.get_product(cursor)
            if cursor_product is None:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, Product, cursor_product)
        return self._page(statement, limit)

    def list_products_for_search(self) -> list[Product]:
        statement = select(Product).order_by(Product.created_at.desc(), Product.id.desc())
        return list(self.session.scalars(statement))

    def create_deal(self, deal: Deal) -> Deal:
        self.session.add(deal)
        self.session.flush()
        return deal

    def get_deal(self, deal_id: str) -> Deal | None:
        return self.session.get(Deal, deal_id)

    def list_deals_for_product(
        self,
        product_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Deal]:
        statement = (
            select(Deal)
            .where(Deal.product_id == product_id)
            .order_by(Deal.created_at.desc(), Deal.id.desc())
        )
        if cursor is not None:
            cursor_deal = self.session.get(Deal, cursor)
            if cursor_deal is None or cursor_deal.product_id != product_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, Deal, cursor_deal)
        return self._page(statement, limit)

    def list_deals_for_search(self) -> list[Deal]:
        statement = select(Deal).order_by(Deal.created_at.desc(), Deal.id.desc())
        return list(self.session.scalars(statement))

    def create_auction(self, auction: Auction) -> Auction:
        self.session.add(auction)
        self.session.flush()
        return auction

    def get_auction(self, auction_id: str) -> Auction | None:
        return self.session.get(Auction, auction_id)

    def get_auction_for_update(self, auction_id: str) -> Auction | None:
        statement = select(Auction).where(Auction.id == auction_id).with_for_update()
        return self.session.scalar(statement)

    def create_auction_bid(self, bid: AuctionBid) -> AuctionBid:
        self.session.add(bid)
        self.session.flush()
        return bid

    def get_highest_auction_bid(self, auction_id: str) -> AuctionBid | None:
        statement = (
            select(AuctionBid)
            .where(AuctionBid.auction_id == auction_id)
            .order_by(
                AuctionBid.amount.desc(),
                AuctionBid.created_at.desc(),
                AuctionBid.id.desc(),
            )
            .limit(1)
        )
        return self.session.scalar(statement)

    def has_auction_bid_from_user(self, *, auction_id: str, user_id: str) -> bool:
        statement = (
            select(AuctionBid.id)
            .where(
                AuctionBid.auction_id == auction_id,
                AuctionBid.user_id == user_id,
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def count_auction_favorites(self, auction_id: str) -> int:
        statement = select(func.count(AuctionFavorite.id)).where(
            AuctionFavorite.auction_id == auction_id
        )
        return self.session.scalar(statement) or 0

    def list_auction_favorite_counts(self) -> dict[str, int]:
        statement = (
            select(AuctionFavorite.auction_id, func.count(AuctionFavorite.id))
            .group_by(AuctionFavorite.auction_id)
            .order_by(AuctionFavorite.auction_id)
        )
        return {auction_id: count for auction_id, count in self.session.execute(statement)}

    def list_auctions_for_product(
        self,
        product_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[Auction]:
        statement = (
            select(Auction)
            .where(Auction.product_id == product_id)
            .order_by(Auction.created_at.desc(), Auction.id.desc())
        )
        if cursor is not None:
            cursor_auction = self.session.get(Auction, cursor)
            if cursor_auction is None or cursor_auction.product_id != product_id:
                raise InvalidSearchCursorException(cursor)
            statement = self._apply_cursor(statement, Auction, cursor_auction)
        return self._page(statement, limit)

    def list_auctions_for_search(self) -> list[Auction]:
        statement = (
            select(Auction)
            .options(selectinload(Auction.bids))
            .order_by(Auction.created_at.desc(), Auction.id.desc())
        )
        return list(self.session.scalars(statement))

    def list_active_auctions_ending_between(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        limit: int,
    ) -> list[Auction]:
        statement = (
            select(Auction)
            .where(
                Auction.status == "active",
                Auction.ends_at.is_not(None),
                Auction.ends_at > starts_at,
                Auction.ends_at <= ends_at,
            )
            .order_by(Auction.ends_at.asc(), Auction.id.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def _page(self, statement: Select[tuple[T]], limit: int) -> CursorPage[T]:
        results = list(self.session.scalars(statement.limit(limit + 1)))
        items = results[:limit]
        next_cursor = items[-1].id if len(results) > limit and items else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def _apply_cursor(
        self,
        statement: Select[tuple[T]],
        model: type[T],
        cursor_item: T,
    ) -> Select[tuple[T]]:
        return statement.where(
            or_(
                model.created_at < cursor_item.created_at,
                and_(model.created_at == cursor_item.created_at, model.id < cursor_item.id),
            )
        )
