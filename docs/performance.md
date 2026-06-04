# Performance

## Load-Test Tool

- Apache JMeter.

## Frontend Verification

- Add Playwright as soon as the frontend app is introduced.
- Use it first for smoke checks in CI: app loads, top search bar renders, API health state is visible.
- Current browser smoke coverage includes search results, AI search entry, favorites,
  OAuth callback hydration, product detail, AI purchase check, verified-review submission
  success and duplicate error handling, auction bidding, My Page, user submissions, and
  admin queues.
- Expand it later to cover mobile layout, visual regression, notification history page,
  and real backend integration smoke checks.

## Scenarios

- Hot-deal spike: many users view and favorite a newly popular deal.
- Auction ending spike: many users view an auction near closing time.
- Search peak: concurrent general search and tab switching for popular terms.

## Initial Goals

- Search API p95 latency target should be measured and tuned after baseline.
- Error rate should remain below an agreed threshold under demo load.
- Kafka consumer lag should recover after spikes.
- Elasticsearch indexing delay should remain visible and measurable.
