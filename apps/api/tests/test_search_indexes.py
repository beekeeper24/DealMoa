from app.modules.search.indexes import SEARCH_INDEXES


def test_search_indexes_use_versioned_names_and_current_aliases() -> None:
    assert SEARCH_INDEXES["products"].index_name == "products_v1"
    assert SEARCH_INDEXES["products"].alias_name == "products_current"
    assert SEARCH_INDEXES["deals"].index_name == "deals_v1"
    assert SEARCH_INDEXES["deals"].alias_name == "deals_current"
    assert SEARCH_INDEXES["auctions"].index_name == "auctions_v1"
    assert SEARCH_INDEXES["auctions"].alias_name == "auctions_current"


def test_product_index_mapping_uses_nori_and_autocomplete_fields() -> None:
    mapping = SEARCH_INDEXES["products"].body

    assert mapping["settings"]["analysis"]["analyzer"]["dealmoa_nori"] == {
        "type": "custom",
        "tokenizer": "nori_tokenizer",
        "filter": ["lowercase"],
    }
    assert mapping["mappings"]["properties"]["name"]["analyzer"] == "dealmoa_nori"
    assert (
        mapping["mappings"]["properties"]["name"]["fields"]["autocomplete"]["analyzer"]
        == "dealmoa_autocomplete"
    )
    assert mapping["mappings"]["properties"]["brand"]["fields"]["keyword"]["type"] == "keyword"
    assert (
        mapping["mappings"]["properties"]["modelName"]["fields"]["keyword"]["type"]
        == "keyword"
    )


def test_offer_index_mappings_keep_status_price_and_product_fields_typed() -> None:
    deal_mapping = SEARCH_INDEXES["deals"].body["mappings"]["properties"]
    auction_mapping = SEARCH_INDEXES["auctions"].body["mappings"]["properties"]

    assert deal_mapping["productId"]["type"] == "keyword"
    assert deal_mapping["status"]["type"] == "keyword"
    assert deal_mapping["salePrice"]["type"] == "integer"
    assert deal_mapping["createdAt"]["type"] == "date"
    assert auction_mapping["productId"]["type"] == "keyword"
    assert auction_mapping["status"]["type"] == "keyword"
    assert auction_mapping["currentPrice"]["type"] == "integer"
    assert auction_mapping["bidCount"]["type"] == "integer"
    assert auction_mapping["uniqueBidderCount"]["type"] == "integer"
    assert auction_mapping["favoriteCount"]["type"] == "integer"
