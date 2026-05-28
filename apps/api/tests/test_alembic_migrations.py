from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def make_alembic_config(database_url: str) -> Config:
    config = Config(str(Path("apps/api/alembic.ini")))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_head_creates_domain_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "dealmoa.db"
    database_url = f"sqlite:///{database_path}"

    command.upgrade(make_alembic_config(database_url), "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= {
        "alembic_version",
        "products",
        "deals",
        "auctions",
        "users",
        "oauth_accounts",
        "refresh_tokens",
        "product_favorites",
        "deal_favorites",
        "auction_favorites",
    }

    deal_foreign_keys = inspector.get_foreign_keys("deals")
    auction_foreign_keys = inspector.get_foreign_keys("auctions")
    oauth_foreign_keys = inspector.get_foreign_keys("oauth_accounts")
    refresh_foreign_keys = inspector.get_foreign_keys("refresh_tokens")
    product_favorite_foreign_keys = inspector.get_foreign_keys("product_favorites")

    assert deal_foreign_keys[0]["referred_table"] == "products"
    assert auction_foreign_keys[0]["referred_table"] == "products"
    assert oauth_foreign_keys[0]["referred_table"] == "users"
    assert refresh_foreign_keys[0]["referred_table"] == "users"
    assert {foreign_key["referred_table"] for foreign_key in product_favorite_foreign_keys} == {
        "users",
        "products",
    }
    assert {"ix_products_name", "ix_deals_product_id", "ix_auctions_product_id"} <= {
        index["name"]
        for table_name in ("products", "deals", "auctions")
        for index in inspector.get_indexes(table_name)
    }
