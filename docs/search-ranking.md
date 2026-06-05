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
GET /api/v1/search/deals/hot?limit=20&cursor=...
GET /api/v1/search/auctions?q=galaxy&limit=20&cursor=...
GET /api/v1/search/auctions/activity?limit=20&cursor=...
POST /api/v1/admin/search/reindex
POST /api/v1/ai/search
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

## Korean Demo Seed And Reindex

Local performance/search demos can seed representative Korean data through:

```bash
uv run python -m app.modules.demo_seed.cli --reindex
```

Inside Docker Compose:

```bash
docker compose --profile core exec api uv run python -m app.modules.demo_seed.cli --reindex
```

The seed command creates or updates a small fixed set of Korean products, hot deals,
auctions, demo users, auction bids, and favorite signals. It is idempotent: repeated runs
reuse existing demo rows by stable model names, source URLs, and demo user IDs instead of
creating duplicates.

`--reindex` calls the existing full search reindex use case after the database seed step.
It does not introduce a second indexing path. This keeps Elasticsearch documents aligned
with the same `SearchUseCases.rebuild_indexes()` behavior used by the admin reindex API.

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

## AI Search Foundation

`POST /api/v1/ai/search` is the first structured AI-search contract. It does not call a
real LLM provider yet. The API parses a deterministic `SearchIntent` and calls existing
product/deal/auction search use cases.

Current intent fields:

- `targetTypes`: allowlisted `products`, `deals`, and `auctions`.
- `filters.category`: small category allowlist from recognized words.
- `filters.maxPrice`: parsed from Korean won expressions such as `100만원`.

The endpoint returns grouped search candidates plus a short deterministic summary. Later
LLM integration should only produce or refine the structured intent; Elasticsearch query
construction must remain allowlist-driven.

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
signal.

The first implemented ranking endpoint is `GET /api/v1/search/deals/hot`.
It filters to `status = active` and scores the Elasticsearch deal read model with
the signals available in the current schema:

- `PriceScore`: capped discount ratio from `originalPrice` and `salePrice`, max 50 points.
  Deals without a valid original price receive zero price-score contribution.
- `InterestScore`: capped `favoriteCount` contribution, max 30 points.
- `FreshnessScore`: linear freshness contribution for deals created inside the 72-hour
  window, max 10 points.
- `TrustScore`: status-derived `trustScore`, max 10 points.

General deal search remains text-relevance dominant and uses status as the visibility gate.
`favoriteCount` is refreshed during full reindex and single deal document upserts. Deal
favorite create/delete event freshness is deferred, so favorite-driven hot-deal ranking
freshness can lag until a reindex or deal document refresh runs.

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
