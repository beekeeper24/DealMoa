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
