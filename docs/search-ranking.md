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
GET /api/v1/search/auctions/activity?limit=20&cursor=...
POST /api/v1/admin/search/reindex
```

Indexes are versioned and queried through aliases:

```text
products_current -> products_v1
deals_current -> deals_v1
auctions_current -> auctions_v1
```

The MVP reindex endpoint rebuilds all three `*_v1` indexes from PostgreSQL and bulk-indexes Product, Deal, and Auction documents. It is intentionally under `/admin/search` so the route shape stays compatible with later admin authentication.

Domain-event indexing also updates single documents:

- `product.updated` upserts the matching `products_current` document.
- `deal.created` upserts the matching `deals_current` document.
- `auction.created` upserts the matching `auctions_current` document.
- `auction.bid.placed` upserts the matching `auctions_current` document so bid-driven ranking signals stay fresh.
- `auction.view.recorded` upserts the matching `auctions_current` document so view-momentum ranking stays fresh.

The admin full reindex endpoint remains the recovery path when mappings change or an index needs rebuilding from PostgreSQL.

Deal and auction search documents carry a status-derived `trustScore` read-model field.
For the current MVP, `active` and `verified` offers receive the full trust score and all
other statuses receive zero. General deal and auction search filters to `status = active`
so admin/status validation can gate visibility without letting report counts directly
affect ranking.

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
The current search read model exposes `trustScore` for deals as a status-derived target
signal. A dedicated hot-deal ranking endpoint is still deferred, so general deal search
keeps text relevance dominant and uses status as the visibility gate.

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

The first implemented activity ranking endpoint is `GET /api/v1/search/auctions/activity`.
It filters to `status = active` and scores the Elasticsearch auction read model with the
signals available in the current schema:

- `BidActivity`: capped `bidCount` contribution, max 45 points.
- `UniqueBidder`: capped `uniqueBidderCount` contribution, max 20 points.
- `ViewMomentum`: capped recent `viewMomentum` contribution from auction detail views in the last 24 hours, max 15 points.
- `Interest`: capped `favoriteCount` contribution, max 10 points.
- `EndingSoon`: auctions ending inside the 24-hour window receive up to 5 points.
- `Trust`: status-derived `trustScore`, max 5 points.

`favoriteCount`, `viewMomentum`, and `trustScore` are refreshed during full reindex and
relevant single-document auction upserts. Reports still do not directly hide or down-rank
content; only status changes from an admin/review workflow affect visibility and trust.
