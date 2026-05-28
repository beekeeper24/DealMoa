from dataclasses import dataclass
from typing import Any, Literal

SearchIndexKind = Literal["products", "deals", "auctions"]


@dataclass(frozen=True)
class SearchIndexSpec:
    index_name: str
    alias_name: str
    body: dict[str, Any]


def base_settings() -> dict[str, Any]:
    return {
        "analysis": {
            "filter": {
                "dealmoa_edge_ngram": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                }
            },
            "analyzer": {
                "dealmoa_nori": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": ["lowercase"],
                },
                "dealmoa_autocomplete": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "dealmoa_edge_ngram"],
                },
            },
        }
    }


def searchable_text_field() -> dict[str, Any]:
    return {
        "type": "text",
        "analyzer": "dealmoa_nori",
        "fields": {
            "autocomplete": {
                "type": "text",
                "analyzer": "dealmoa_autocomplete",
                "search_analyzer": "dealmoa_nori",
            },
            "keyword": {"type": "keyword"},
        },
    }


PRODUCT_INDEX_BODY: dict[str, Any] = {
    "settings": base_settings(),
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "name": searchable_text_field(),
            "brand": searchable_text_field(),
            "modelName": searchable_text_field(),
            "category": searchable_text_field(),
            "specsText": {"type": "text", "analyzer": "dealmoa_nori"},
            "createdAt": {"type": "date"},
            "updatedAt": {"type": "date"},
        },
    },
}

DEAL_INDEX_BODY: dict[str, Any] = {
    "settings": base_settings(),
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "productId": {"type": "keyword"},
            "title": searchable_text_field(),
            "seller": searchable_text_field(),
            "sourceUrl": {"type": "keyword", "index": False},
            "originalPrice": {"type": "integer"},
            "salePrice": {"type": "integer"},
            "currency": {"type": "keyword"},
            "status": {"type": "keyword"},
            "startedAt": {"type": "date"},
            "endedAt": {"type": "date"},
            "createdAt": {"type": "date"},
            "updatedAt": {"type": "date"},
        },
    },
}

AUCTION_INDEX_BODY: dict[str, Any] = {
    "settings": base_settings(),
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "productId": {"type": "keyword"},
            "title": searchable_text_field(),
            "seller": searchable_text_field(),
            "sourceUrl": {"type": "keyword", "index": False},
            "currentPrice": {"type": "integer"},
            "bidCount": {"type": "integer"},
            "uniqueBidderCount": {"type": "integer"},
            "currency": {"type": "keyword"},
            "status": {"type": "keyword"},
            "endsAt": {"type": "date"},
            "createdAt": {"type": "date"},
            "updatedAt": {"type": "date"},
        },
    },
}

SEARCH_INDEXES: dict[SearchIndexKind, SearchIndexSpec] = {
    "products": SearchIndexSpec(
        index_name="products_v1",
        alias_name="products_current",
        body=PRODUCT_INDEX_BODY,
    ),
    "deals": SearchIndexSpec(
        index_name="deals_v1",
        alias_name="deals_current",
        body=DEAL_INDEX_BODY,
    ),
    "auctions": SearchIndexSpec(
        index_name="auctions_v1",
        alias_name="auctions_current",
        body=AUCTION_INDEX_BODY,
    ),
}
