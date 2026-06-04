# DealMoa Planning

## Concept

딜모아는 핫딜과 경매 상품을 수집하고, Elasticsearch 기반 한국어 검색과 랭킹 시스템으로 사용자가 좋은 구매 기회를 탐색하도록 돕는 커머스 플랫폼이다.

직접 결제/주문을 처리하는 쇼핑몰이 아니라, 상품 기준으로 현재 딜, 경매, 가격 히스토리, 구매 인증 후기, 토론, 관심 알림, AI 구매 보조를 모아주는 검색 중심 서비스다.

## Core Positioning

- 포트폴리오 핵심 축은 검색/추천/랭킹 백엔드다.
- 주요 어필 포인트는 Elasticsearch, Nori 기반 한국어 검색, 랭킹, 이벤트 기반 알림, 백그라운드 파이프라인, AI 검색/구매 보조, 관측성, 부하 테스트다.
- 단순 쇼핑몰 CRUD나 결제 서비스로 포지셔닝하지 않는다.

## Key Features

- 기본 검색: 상품명, 브랜드, 모델명, 카테고리, 스펙 기반 텍스트 검색.
- 검색 결과 탭: 상품, 핫딜, 경매.
- AI 검색: 검색창 옆 AI 버튼으로 실행하고, 플로팅 챗봇을 기본 UX로 두지 않는다.
- 관심 등록: 상품, 딜, 경매 각각 관심 등록 가능.
- 상품 관심 알림: 관심 상품과 관련된 새 딜/새 경매가 등록되면 알림 생성.
- 경매 관심 알림: 관심 경매 종료 임박 알림.
- 홈 화면: 현재 진행 중인 경매 중 활성도가 높은 항목을 회전초밥 느낌의 가로 레일로 노출.
- 핫딜 랭킹: 가격 점수를 가장 크게 보고 관심도와 신뢰도를 보조 지표로 사용.
- 경매 랭킹: 관심도보다 실제 입찰 활성도를 우선한다.
- 구매 인증 후기: 사이트 구매내역 또는 영수증 기반 인증. MVP 초기에는 정상 제출을 자동 공개하고, 플랫폼 위험 신호나 관리자 판단 건만 사후 검수한다. 플랫폼 위험 신호는 관리자 우선순위 신호일 뿐 자동 숨김/감점에 쓰지 않는다. 소비자 신고 버튼은 MVP 우선순위에서 제외한다.
- 사용자 제보: 자동 게시하지 않고 AI 1차 검수 후 관리자 승인.
- 커뮤니티: 자유게시판 중심이 아니라 상품별 토론/후기 흐름을 둔다.
- 관리자: 제보, 플랫폼 위험 신호가 있는 인증 후기, 상품 매칭, 신고, 크롤러 로그, 수동 등록을 관리.
- 모니터링/부하 테스트: Prometheus/Grafana와 JMeter로 트래픽 집중 상황을 검증.

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui.
- Backend: FastAPI, Python, Pydantic, SQLAlchemy, Alembic.
- Deployment: Vercel for `apps/web`, Railway for API and backend services.
- Database: PostgreSQL.
- Search: Elasticsearch with Nori analyzer.
- Events: Kafka.
- Jobs: Celery + Redis.
- Observability: Prometheus, Grafana.
- Load test: JMeter.
- Auth: Google, Kakao, Naver OAuth from the first pass.

## Package And Workspace Tooling

- Python dependency and environment management: `uv`.
- Python version target: `3.12` unless a core dependency forces a downgrade.
- Node/frontend package manager: `pnpm` with a root `pnpm-workspace.yaml`.
- Python apps are managed through a `uv` workspace when `apps/api`, `apps/worker`, and `apps/consumer` become separate Python packages.
- Frontend packages are managed through `pnpm` workspaces, starting with `apps/web`.
- Do not introduce Turborepo/Nx in the first scaffold. Add it only if command orchestration becomes painful.

## Environment Strategy

- Use a root `.env` as the local runtime source.
- Keep `.env` and `.env.*` ignored by Git.
- Commit `.env.example` to document required variables without secrets.
- Do not create app-level `.env` files in the first scaffold unless a tool requires it.
- Use clear prefixes such as `API_`, `WEB_`, `OAUTH_`, `ELASTICSEARCH_`, `KAFKA_`, and `REDIS_`.
- Production variable names should match Vercel/Railway runtime names. Local-only aliases are allowed only as compatibility shims.

## Quality And CI

- Introduce CI from the first implementation milestone.
- Start with lightweight lint, typecheck, and unit tests.
- Backend quality tools: ruff, mypy, pytest.
- Frontend quality tools: eslint, prettier, TypeScript typecheck, Vitest.
- Add Playwright as soon as the frontend app is introduced so browser smoke/e2e checks can enter CI early.
- Add Elasticsearch, Kafka, Celery, and observability integration checks as those systems are implemented.

## Ranking

- `HotDealScore = PriceScore 50 + InterestScore 30 + FreshnessScore 10 + TrustScore 10`.
- `AuctionActivityScore = BidActivity 45 + UniqueBidder 20 + ViewMomentum 15 + Interest 10 + EndingSoon 5 + Trust 5`.
- 신고 수는 자동 감점/숨김에 직접 사용하지 않고 관리자 검토 큐로 보낸다.
- 일반 검색은 텍스트 관련도 중심이며 기본 경로에 벡터 검색을 넣지 않는다.
- AI 검색은 구조화된 intent, 필터, BM25, vector 후보 검색, 설명 생성을 조합한다.

## Screen Flow

- Shared top bar: logo, search input, search button, AI button, notification icon, avatar.
- Home: active auction rail, today hot deals, right-side recent-viewed floating sidebar.
- Search: product/deal/auction tabs.
- Product detail: summary, price history, current deals, current auctions, AI purchase check, verified reviews, discussion, alternatives, favorite.
- Deal detail: price/conditions, linked product, external link, favorite, discussion, report.
- Auction detail: current price, bid count, remaining time, external link, favorite, discussion, report.
- My page: favorites, notifications, submissions, verified reviews, connected accounts.
- Admin: dashboard, submissions, verified review post-moderation, manual registration, product merge/matching, crawler logs, reports.

## Milestones

1. Project foundation: monorepo structure, uv/pnpm workspaces, root `.env.example`, Docker Compose core profile, FastAPI health API, Next.js shell, PostgreSQL, Redis, Elasticsearch + Nori, CI.
2. Product/search basics: Product, Deal, Auction CRUD, Elasticsearch indexing, product/deal/auction search, cursor pagination.
3. Auth/favorites/notifications: Google/Kakao/Naver OAuth, access/refresh tokens, favorites, new deal/auction alerts, auction ending-soon alerts, notification popup API, my page lists.
4. Admin/submission/review workflow: user submissions, AI first-pass mock, admin approval/rejection, crawler mock batch, admin product matching, report review.
5. Ranking/price history/verified reviews: HotDealScore, AuctionActivityScore, price history, verified purchase reviews, receipt/order-history based auto-publish review path, post-publication moderation, product discussion.
6. AI search/purchase assistant: AI search button, SearchIntent validation, Elasticsearch multi-search, vector candidate search, purchase check report based on verified reviews.
7. Observability/load test/hardening: Prometheus/Grafana, JMeter scenarios, Kafka/Celery hardening, expanded Playwright e2e, operational docs.

## Exclusions

- No automatic publishing of user submissions.
- No direct use of report counts for automatic down-ranking/hiding.
- No community sentiment summary as a purchase fact.
- No floating chatbot as the primary AI interface.
- No search-result caching in the initial version.
