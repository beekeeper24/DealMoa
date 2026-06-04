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
        "notifications",
        "domain_events",
        "auction_bids",
        "auction_views",
        "admin_audit_logs",
        "offer_reports",
        "submissions",
        "price_history_snapshots",
        "verified_reviews",
        "product_discussion_comments",
        "crawler_run_logs",
        "ai_review_usage_events",
    }

    deal_foreign_keys = inspector.get_foreign_keys("deals")
    auction_foreign_keys = inspector.get_foreign_keys("auctions")
    oauth_foreign_keys = inspector.get_foreign_keys("oauth_accounts")
    refresh_foreign_keys = inspector.get_foreign_keys("refresh_tokens")
    product_favorite_foreign_keys = inspector.get_foreign_keys("product_favorites")
    notification_foreign_keys = inspector.get_foreign_keys("notifications")
    auction_bid_foreign_keys = inspector.get_foreign_keys("auction_bids")
    auction_view_foreign_keys = inspector.get_foreign_keys("auction_views")
    domain_event_indexes = {index["name"] for index in inspector.get_indexes("domain_events")}
    auction_bid_indexes = {index["name"] for index in inspector.get_indexes("auction_bids")}
    auction_view_indexes = {index["name"] for index in inspector.get_indexes("auction_views")}
    admin_audit_indexes = {
        index["name"] for index in inspector.get_indexes("admin_audit_logs")
    }
    offer_report_indexes = {index["name"] for index in inspector.get_indexes("offer_reports")}
    submission_indexes = {index["name"] for index in inspector.get_indexes("submissions")}
    price_history_indexes = {
        index["name"] for index in inspector.get_indexes("price_history_snapshots")
    }
    verified_review_indexes = {
        index["name"] for index in inspector.get_indexes("verified_reviews")
    }
    discussion_indexes = {
        index["name"] for index in inspector.get_indexes("product_discussion_comments")
    }
    discussion_columns = {
        column["name"] for column in inspector.get_columns("product_discussion_comments")
    }
    crawler_run_log_indexes = {
        index["name"] for index in inspector.get_indexes("crawler_run_logs")
    }
    crawler_run_log_columns = {
        column["name"] for column in inspector.get_columns("crawler_run_logs")
    }
    ai_review_usage_indexes = {
        index["name"] for index in inspector.get_indexes("ai_review_usage_events")
    }

    assert deal_foreign_keys[0]["referred_table"] == "products"
    assert auction_foreign_keys[0]["referred_table"] == "products"
    assert oauth_foreign_keys[0]["referred_table"] == "users"
    assert refresh_foreign_keys[0]["referred_table"] == "users"
    assert {foreign_key["referred_table"] for foreign_key in product_favorite_foreign_keys} == {
        "users",
        "products",
    }
    assert notification_foreign_keys[0]["referred_table"] == "users"
    assert {foreign_key["referred_table"] for foreign_key in auction_bid_foreign_keys} == {
        "auctions",
        "users",
    }
    assert auction_view_foreign_keys[0]["referred_table"] == "auctions"
    assert inspector.get_foreign_keys("admin_audit_logs")[0]["referred_table"] == "users"
    assert inspector.get_foreign_keys("offer_reports")[0]["referred_table"] == "users"
    assert {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("submissions")
    } == {"users"}
    assert inspector.get_foreign_keys("price_history_snapshots")[0]["referred_table"] == "products"
    assert {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("verified_reviews")
    } == {"products", "users"}
    assert {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("product_discussion_comments")
    } == {"products", "users"}
    assert {
        "ix_domain_events_published_at_created_at",
        "ix_domain_events_event_type",
        "ix_domain_events_aggregate",
    } <= domain_event_indexes
    assert {"ix_auction_bids_auction_id", "ix_auction_bids_user_id"} <= auction_bid_indexes
    assert {"ix_auction_views_auction_id_created_at"} <= auction_view_indexes
    assert {
        "ix_admin_audit_logs_actor_user_id_created_at",
        "ix_admin_audit_logs_target",
        "ix_admin_audit_logs_action_created_at",
    } <= admin_audit_indexes
    assert {
        "ix_offer_reports_status_created_at",
        "ix_offer_reports_target",
        "ix_offer_reports_user_target_status",
    } <= offer_report_indexes
    assert {
        "ix_submissions_status_created_at",
        "ix_submissions_user_id_created_at",
        "ix_submissions_source_url",
    } <= submission_indexes
    assert {
        "ix_price_history_product_observed_at",
        "ix_price_history_source",
    } <= price_history_indexes
    assert {
        "ix_verified_reviews_product_status_created_at",
        "ix_verified_reviews_status_created_at",
        "ix_verified_reviews_user_id_created_at",
    } <= verified_review_indexes
    assert {
        "ix_product_discussion_comments_product_status_created_at",
        "ix_product_discussion_comments_status_created_at",
        "ix_product_discussion_comments_user_id_created_at",
        "ix_product_discussion_comments_status_risk_created_at",
    } <= discussion_indexes
    assert {
        "moderation_risk_score",
        "moderation_risk_level",
        "moderation_risk_reasons_json",
    } <= discussion_columns
    assert {
        "ix_crawler_run_logs_created_at",
        "ix_crawler_run_logs_task_name_created_at",
        "ix_crawler_run_logs_status_created_at",
    } <= crawler_run_log_indexes
    assert {"error_type", "error_message"} <= crawler_run_log_columns
    assert {
        "ix_ai_review_usage_events_user_id_created_at",
        "ix_ai_review_usage_events_user_target_created_at",
    } <= ai_review_usage_indexes
    assert {"ix_products_name", "ix_deals_product_id", "ix_auctions_product_id"} <= {
        index["name"]
        for table_name in ("products", "deals", "auctions")
        for index in inspector.get_indexes(table_name)
    }
