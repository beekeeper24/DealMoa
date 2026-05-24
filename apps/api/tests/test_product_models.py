from typing import cast

from app.db.base import Base
from app.modules.products.models import Auction, Deal, Product
from sqlalchemy import ForeignKeyConstraint, Index, Table, inspect


def test_product_deal_auction_tables_are_registered() -> None:
    assert Base.metadata.tables.keys() >= {"products", "deals", "auctions"}
    assert Product.__tablename__ == "products"
    assert Deal.__tablename__ == "deals"
    assert Auction.__tablename__ == "auctions"


def test_product_columns_capture_search_identity() -> None:
    product = cast(Table, Product.__table__)

    assert set(product.columns.keys()) == {
        "id",
        "name",
        "brand",
        "model_name",
        "category",
        "specs",
        "created_at",
        "updated_at",
    }
    assert not product.c.name.nullable
    assert product.c.brand.nullable
    assert product.c.model_name.nullable
    assert product.c.specs.nullable


def test_deal_and_auction_reference_product_identity() -> None:
    for table in (cast(Table, Deal.__table__), cast(Table, Auction.__table__)):
        foreign_keys = [
            constraint
            for constraint in table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        ]

        assert len(foreign_keys) == 1
        assert foreign_keys[0].referred_table.name == "products"
        assert table.c.product_id.nullable is False


def test_offer_tables_have_status_and_price_fields() -> None:
    deal_columns = set(Deal.__table__.columns.keys())
    auction_columns = set(Auction.__table__.columns.keys())

    assert {
        "id",
        "product_id",
        "title",
        "source_url",
        "seller",
        "original_price",
        "sale_price",
        "currency",
        "status",
        "started_at",
        "ended_at",
        "created_at",
        "updated_at",
    } <= deal_columns
    assert {
        "id",
        "product_id",
        "title",
        "source_url",
        "seller",
        "current_price",
        "bid_count",
        "currency",
        "status",
        "ends_at",
        "created_at",
        "updated_at",
    } <= auction_columns

    assert Deal.__table__.c.sale_price.nullable is False
    assert Auction.__table__.c.current_price.nullable is False


def test_product_module_indexes_support_lookup_and_join_paths() -> None:
    expected_indexes = {
        "ix_products_name",
        "ix_products_brand",
        "ix_products_model_name",
        "ix_deals_product_id",
        "ix_deals_status",
        "ix_auctions_product_id",
        "ix_auctions_status",
    }
    indexes = {
        index.name
        for table in (
            cast(Table, Product.__table__),
            cast(Table, Deal.__table__),
            cast(Table, Auction.__table__),
        )
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert expected_indexes <= indexes


def test_product_relationships_are_bidirectional() -> None:
    product_relationships = inspect(Product).relationships
    deal_relationships = inspect(Deal).relationships
    auction_relationships = inspect(Auction).relationships

    assert product_relationships.deals.mapper.class_ is Deal
    assert product_relationships.auctions.mapper.class_ is Auction
    assert deal_relationships.product.mapper.class_ is Product
    assert auction_relationships.product.mapper.class_ is Product
