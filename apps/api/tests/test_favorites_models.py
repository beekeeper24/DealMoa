from typing import cast

from app.db.base import Base
from app.modules.favorites.models import AuctionFavorite, DealFavorite, ProductFavorite
from sqlalchemy import ForeignKeyConstraint, Index, Table, UniqueConstraint, inspect


def test_favorite_tables_are_registered() -> None:
    assert Base.metadata.tables.keys() >= {
        "product_favorites",
        "deal_favorites",
        "auction_favorites",
    }
    assert ProductFavorite.__tablename__ == "product_favorites"
    assert DealFavorite.__tablename__ == "deal_favorites"
    assert AuctionFavorite.__tablename__ == "auction_favorites"


def test_favorite_tables_are_unique_per_user_and_target() -> None:
    expected = {
        ProductFavorite: ("user_id", "product_id"),
        DealFavorite: ("user_id", "deal_id"),
        AuctionFavorite: ("user_id", "auction_id"),
    }

    for model, columns in expected.items():
        table = cast(Table, model.__table__)
        unique_columns = {
            tuple(constraint.columns.keys())
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }

        assert columns in unique_columns


def test_favorite_tables_reference_user_and_target_tables() -> None:
    expected_targets = {
        ProductFavorite: "products",
        DealFavorite: "deals",
        AuctionFavorite: "auctions",
    }

    for model, target_table in expected_targets.items():
        table = cast(Table, model.__table__)
        referred_tables = {
            constraint.referred_table.name
            for constraint in table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        }

        assert referred_tables == {"users", target_table}
        assert table.c.user_id.nullable is False


def test_favorite_indexes_support_user_lists() -> None:
    expected_indexes = {
        "ix_product_favorites_user_id",
        "ix_deal_favorites_user_id",
        "ix_auction_favorites_user_id",
    }
    indexes = {
        index.name
        for table in (
            cast(Table, ProductFavorite.__table__),
            cast(Table, DealFavorite.__table__),
            cast(Table, AuctionFavorite.__table__),
        )
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert expected_indexes <= indexes


def test_favorite_relationships_are_bidirectional() -> None:
    assert inspect(ProductFavorite).relationships.user.mapper.class_.__name__ == "User"
    assert inspect(ProductFavorite).relationships.product.mapper.class_.__name__ == "Product"
    assert inspect(DealFavorite).relationships.deal.mapper.class_.__name__ == "Deal"
    assert inspect(AuctionFavorite).relationships.auction.mapper.class_.__name__ == "Auction"
