# Search And Ranking

## General Search

General search is for exact product discovery: product name, brand, model, category, and specs.

- Use BM25/Nori/exact/ngram/synonym/limited fuzzy.
- Do not use vector search by default.
- Model and brand exact matches must dominate popularity and price signals.

## Search Correction

- Normalize lowercase, spaces, hyphens, and common model patterns.
- Use Nori analyzer for Korean product names and deal titles.
- Use exact keyword fields for brand/model.
- Use ngram/search-as-you-type for partial input.
- Use synonym/alias dictionaries for Korean/English brand and product names.
- Use fuzzy only as fallback and avoid aggressive fuzzy on short model names.

## Search API MVP

The first search slice exposes Elasticsearch-backed read APIs while PostgreSQL remains the source of truth.

Routes use the `/api/v1` prefix:

```http
GET /api/v1/search/products?q=galaxy&limit=20&cursor=...
GET /api/v1/search/deals?q=galaxy&limit=20&cursor=...
GET /api/v1/search/auctions?q=galaxy&limit=20&cursor=...
POST /api/v1/admin/search/reindex
```

Indexes are versioned and queried through aliases:

```text
products_current -> products_v1
deals_current -> deals_v1
auctions_current -> auctions_v1
```

The MVP reindex endpoint rebuilds all three `*_v1` indexes from PostgreSQL and bulk-indexes Product, Deal, and Auction documents. It is intentionally under `/admin/search` so the route shape stays compatible with later admin authentication.

Search list responses use the same response envelope shape as Product API lists:

```json
{
  "items": [],
  "nextCursor": null
}
```

Search cursors encode Elasticsearch `search_after` sort values. Clients should treat them as opaque strings and pass them back unchanged.

## Hot Deal Ranking

```text
HotDealScore =
PriceScore 50
+ InterestScore 30
+ FreshnessScore 10
+ TrustScore 10
```

Reports do not directly lower rank. They only prioritize admin review.

## Auction Activity Ranking

```text
AuctionActivityScore =
BidActivity 45
+ UniqueBidder 20
+ ViewMomentum 15
+ Interest 10
+ EndingSoon 5
+ Trust 5
```

The home auction rail should show auctions that are actively moving, not hidden opportunities.
