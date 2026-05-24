# Performance

## Load-Test Tool

- Apache JMeter.

## Scenarios

- Hot-deal spike: many users view and favorite a newly popular deal.
- Auction ending spike: many users view an auction near closing time.
- Search peak: concurrent general search and tab switching for popular terms.

## Initial Goals

- Search API p95 latency target should be measured and tuned after baseline.
- Error rate should remain below an agreed threshold under demo load.
- Kafka consumer lag should recover after spikes.
- Elasticsearch indexing delay should remain visible and measurable.
