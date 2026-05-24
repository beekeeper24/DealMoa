# DealMoa Planning

## Concept

딜모아는 핫딜과 경매 상품을 수집하고, Elasticsearch 기반 한국어 검색과 랭킹 시스템으로 사용자가 좋은 구매 기회를 탐색하도록 돕는 커머스 플랫폼이다.

## Core Positioning

- Search/recommendation backend portfolio project.
- Main strengths: Elasticsearch, Korean search quality, ranking, event-driven alerts, background pipelines, AI-assisted search/checks, observability, load testing.
- Not a direct checkout/payment shopping mall.

## Key Features

- Basic search for product name, brand, model, category, and specs.
- Search result tabs: products, hot deals, auctions.
- AI search via search-bar-side AI button, not a floating chatbot.
- Product, deal, and auction favorites.
- Product favorite alerts for new related deals and auctions.
- Auction favorite ending-soon alerts.
- Hot-deal ranking based on price and interest.
- Home auction rail based on auction activity.
- Verified purchase reviews with AI first-pass review and admin approval.
- User submissions with AI first-pass review and admin approval.
- Admin tools for submissions, reviews, product matching, reports, crawler logs, and manual deal/auction registration.
- Prometheus/Grafana monitoring and JMeter load-test scenarios.

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui.
- Backend: FastAPI, Python, Pydantic, SQLAlchemy, Alembic.
- Database: PostgreSQL.
- Search: Elasticsearch with Nori analyzer.
- Events: Kafka.
- Jobs: Celery + Redis.
- Observability: Prometheus, Grafana.
- Load test: JMeter.
- Auth: Google, Kakao, Naver OAuth from the first pass.

## Ranking

- `HotDealScore = PriceScore 50 + InterestScore 30 + FreshnessScore 10 + TrustScore 10`.
- `AuctionActivityScore = BidActivity 45 + UniqueBidder 20 + ViewMomentum 15 + Interest 10 + EndingSoon 5 + Trust 5`.
- General search is text relevance first and does not use vector search by default.
- AI search uses structured intent parsing, filters, BM25, vector search, and explanation.

## Screen Flow

- Shared top bar: logo, search input, search button, AI button, notification icon, avatar.
- Home: active auction rail, today hot deals, right-side recent-viewed floating sidebar.
- Search: product/deal/auction tabs.
- Product detail: summary, price history, current deals, current auctions, AI purchase check, verified reviews, discussion, alternatives.
- Deal detail: price/conditions, linked product, external link, favorite, discussion, report.
- Auction detail: current price, bid count, remaining time, external link, favorite, discussion, report.
- My page: favorites, notifications, submissions, verified reviews, connected accounts.
- Admin: dashboard, submissions, verified review queue, manual registration, product merge/matching, crawler logs, reports.

## Exclusions

- No automatic publishing of user submissions.
- No direct use of report counts for automatic down-ranking/hiding.
- No community sentiment summary as a purchase fact.
- No floating chatbot as primary AI interface.
- No search-result caching in the initial version.
