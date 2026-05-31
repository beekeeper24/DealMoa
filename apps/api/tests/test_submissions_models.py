from app.db.base import Base
from app.modules.submissions import models as submission_models  # noqa: F401


def test_submission_table_contract() -> None:
    table = Base.metadata.tables["submissions"]

    assert {
        "id",
        "user_id",
        "offer_type",
        "source_url",
        "product_name",
        "brand",
        "model_name",
        "category",
        "title",
        "seller",
        "original_price",
        "sale_price",
        "current_price",
        "currency",
        "description",
        "status",
        "ai_decision",
        "ai_reason",
        "ai_reviewed_at",
        "reviewed_by_user_id",
        "resolution_note",
        "resolved_at",
        "published_product_id",
        "published_offer_type",
        "published_offer_id",
        "created_at",
        "updated_at",
    } <= set(table.columns.keys())

    assert table.columns["user_id"].foreign_keys
    assert table.columns["reviewed_by_user_id"].foreign_keys
    assert table.columns["source_url"].nullable is False
