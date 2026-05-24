# Search Index MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Elasticsearch-backed search slice for Product, Deal, and Auction data.

**Architecture:** PostgreSQL remains the source of truth. The API owns search read access and a small rebuild path for the MVP, while future Kafka/Celery work can reuse the same document builders and index specs. Search routes stay thin and call a use-case layer backed by an Elasticsearch REST adapter.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, httpx, Elasticsearch REST API, Nori analyzer, pytest, ruff, mypy.

---

### Task 1: Search Contract And Index Specs

**Files:**
- Create: `apps/api/app/modules/search/indexes.py`
- Create: `apps/api/tests/test_search_indexes.py`
- Modify: `docs/search-ranking.md`

- [ ] **Step 1: Write failing tests for index names, aliases, and Nori settings**

```python
from app.modules.search.indexes import SEARCH_INDEXES


def test_search_indexes_use_versioned_names_and_current_aliases() -> None:
    assert SEARCH_INDEXES["products"].index_name == "products_v1"
    assert SEARCH_INDEXES["products"].alias_name == "products_current"
    assert SEARCH_INDEXES["deals"].index_name == "deals_v1"
    assert SEARCH_INDEXES["auctions"].index_name == "auctions_v1"


def test_product_index_mapping_uses_nori_and_autocomplete_fields() -> None:
    mapping = SEARCH_INDEXES["products"].body

    assert mapping["settings"]["analysis"]["analyzer"]["dealmoa_nori"]["tokenizer"] == "nori_tokenizer"
    assert mapping["mappings"]["properties"]["name"]["analyzer"] == "dealmoa_nori"
    assert mapping["mappings"]["properties"]["name"]["fields"]["autocomplete"]["analyzer"] == "dealmoa_autocomplete"
```

- [ ] **Step 2: Run test to verify RED**

Run: `uv run pytest apps/api/tests/test_search_indexes.py -q`
Expected: FAIL because `app.modules.search` does not exist.

- [ ] **Step 3: Implement index specs**

Create `SearchIndexSpec` values for `products`, `deals`, and `auctions` with versioned index names, current aliases, Nori analyzer, autocomplete analyzer, exact keyword fields, and typed price/status/date fields.

- [ ] **Step 4: Run test to verify GREEN**

Run: `uv run pytest apps/api/tests/test_search_indexes.py -q`
Expected: PASS.

### Task 2: Search Documents And Rebuild Use Case

**Files:**
- Create: `apps/api/app/modules/search/documents.py`
- Create: `apps/api/app/modules/search/repository.py`
- Create: `apps/api/app/modules/search/use_cases.py`
- Create: `apps/api/tests/test_search_documents.py`
- Modify: `apps/api/app/modules/products/repository.py`

- [ ] **Step 1: Write failing tests for Product/Deal/Auction document conversion**

```python
from datetime import UTC, datetime

from app.modules.products.models import Product
from app.modules.search.documents import build_product_document


def test_product_search_document_flattens_specs_for_text_search() -> None:
    product = Product(
        id="product-1",
        name="Galaxy S26 Ultra",
        brand="Samsung",
        model_name="SM-S260",
        category="smartphone",
        specs={"storage": "256GB", "색상": "블랙"},
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
        updated_at=datetime(2026, 5, 25, tzinfo=UTC),
    )

    document = build_product_document(product)

    assert document["id"] == "product-1"
    assert document["modelName"] == "SM-S260"
    assert document["specsText"] == "storage 256GB 색상 블랙"
    assert document["createdAt"] == "2026-05-25T00:00:00Z"
```

- [ ] **Step 2: Run test to verify RED**

Run: `uv run pytest apps/api/tests/test_search_documents.py -q`
Expected: FAIL because document builders do not exist.

- [ ] **Step 3: Implement document builders and source repository methods**

Add deterministic document builders for Product, Deal, and Auction. Add repository methods that list all rows ordered by `created_at desc, id desc` for rebuild.

- [ ] **Step 4: Run test to verify GREEN**

Run: `uv run pytest apps/api/tests/test_search_documents.py -q`
Expected: PASS.

### Task 3: Elasticsearch Adapter And Search API

**Files:**
- Create: `apps/api/app/modules/search/client.py`
- Create: `apps/api/app/modules/search/router.py`
- Create: `apps/api/app/modules/search/schemas.py`
- Create: `apps/api/tests/test_search_api.py`
- Modify: `apps/api/app/api/v1/router.py`
- Modify: `apps/api/app/core/exceptions.py`
- Modify: `docs/product-api.md`

- [ ] **Step 1: Write failing API tests with a fake search use case**

```python
from app.modules.search.router import get_search_use_cases


def test_search_products_returns_items_and_next_cursor() -> None:
    client = make_search_test_client(FakeSearchUseCases())

    response = client.get("/api/v1/search/products?q=galaxy&limit=1")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "product-1"
    assert response.json()["nextCursor"] == "cursor-2"
```

- [ ] **Step 2: Run test to verify RED**

Run: `uv run pytest apps/api/tests/test_search_api.py -q`
Expected: FAIL because search router does not exist.

- [ ] **Step 3: Implement schemas, router, use case, and REST adapter**

Add `GET /api/v1/search/products`, `/search/deals`, and `/search/auctions` with `q`, `limit`, and `cursor`. The Elasticsearch adapter should create indexes, bulk replace documents for rebuild, and search aliases with `search_after` cursors.

- [ ] **Step 4: Run API tests to verify GREEN**

Run: `uv run pytest apps/api/tests/test_search_api.py -q`
Expected: PASS.

### Task 4: Runtime Verification And Documentation

**Files:**
- Modify: `docs/search-ranking.md`
- Modify: `docs/handoff.md`
- Modify: `.gitignore`

- [ ] **Step 1: Run backend verification**

Run:
```bash
uv run ruff check apps/api
uv run mypy apps/api/app apps/api/tests
uv run pytest apps/api/tests
```

- [ ] **Step 2: Run frontend and compose smoke checks**

Run:
```bash
pnpm --filter @dealmoa/web lint
pnpm --filter @dealmoa/web typecheck
pnpm --filter @dealmoa/web test
pnpm --filter @dealmoa/web build
docker compose --profile core config
```

- [ ] **Step 3: Run local Elasticsearch runtime check**

Start Elasticsearch on a free host port if needed, run the API search rebuild path against seeded Product/Deal/Auction data, and verify a product/deal/auction search query returns expected results.

- [ ] **Step 4: Commit checkpoint**

Commit the verified search MVP and `.idea/` ignore cleanup together on `feature/search-index-mvp`. Do not open a PR unless the user explicitly asks or the slice is ready and the user confirms integration.
