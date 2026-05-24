from collections.abc import Iterator
from typing import cast

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.products import models as product_models  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def make_test_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app()

    def override_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def create_product(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Galaxy S26",
            "brand": "Samsung",
            "modelName": "SM-S260",
            "category": "smartphone",
            "specs": {"storage": "256GB"},
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def test_create_and_get_product() -> None:
    client = make_test_client()

    created = create_product(client)
    response = client.get(f"/api/v1/products/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_list_products_returns_created_products() -> None:
    client = make_test_client()

    created = create_product(client)
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.json()["items"] == [created]
    assert response.json()["nextCursor"] is None


def test_list_products_supports_cursor_pagination() -> None:
    client = make_test_client()
    first = create_product(client)
    second = create_product(client)
    third = create_product(client)

    first_page = client.get("/api/v1/products?limit=2")
    second_page = client.get(f"/api/v1/products?limit=2&cursor={first_page.json()['nextCursor']}")

    assert first_page.status_code == 200
    assert [item["id"] for item in first_page.json()["items"]] == [third["id"], second["id"]]
    assert first_page.json()["nextCursor"] == second["id"]
    assert second_page.status_code == 200
    assert [item["id"] for item in second_page.json()["items"]] == [first["id"]]
    assert second_page.json()["nextCursor"] is None


def test_invalid_product_cursor_uses_common_error_shape() -> None:
    client = make_test_client()

    response = client.get("/api/v1/products?cursor=not-a-product")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SEARCH_CURSOR"


def test_create_and_list_product_deals() -> None:
    client = make_test_client()
    product = create_product(client)

    create_response = client.post(
        f"/api/v1/products/{product['id']}/deals",
        json={
            "title": "Galaxy S26 launch deal",
            "sourceUrl": "https://example.com/deals/galaxy-s26",
            "seller": "Example Store",
            "originalPrice": 1400000,
            "salePrice": 1090000,
            "currency": "KRW",
            "status": "active",
        },
    )
    list_response = client.get(f"/api/v1/products/{product['id']}/deals")

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["productId"] == product["id"]
    assert created["salePrice"] == 1090000
    assert list_response.status_code == 200
    assert list_response.json()["items"] == [created]
    assert list_response.json()["nextCursor"] is None


def test_list_product_deals_supports_cursor_pagination() -> None:
    client = make_test_client()
    product = create_product(client)

    created_deals: list[dict[str, object]] = []
    for index in range(3):
        response = client.post(
            f"/api/v1/products/{product['id']}/deals",
            json={
                "title": f"Galaxy S26 launch deal {index}",
                "sourceUrl": f"https://example.com/deals/galaxy-s26-{index}",
                "salePrice": 1090000 + index,
            },
        )
        assert response.status_code == 201
        created_deals.append(response.json())

    first_page = client.get(f"/api/v1/products/{product['id']}/deals?limit=2")
    second_page = client.get(
        f"/api/v1/products/{product['id']}/deals?limit=2"
        f"&cursor={first_page.json()['nextCursor']}"
    )

    assert [item["id"] for item in first_page.json()["items"]] == [
        created_deals[2]["id"],
        created_deals[1]["id"],
    ]
    assert first_page.json()["nextCursor"] == created_deals[1]["id"]
    assert [item["id"] for item in second_page.json()["items"]] == [created_deals[0]["id"]]


def test_create_and_list_product_auctions() -> None:
    client = make_test_client()
    product = create_product(client)

    create_response = client.post(
        f"/api/v1/products/{product['id']}/auctions",
        json={
            "title": "Galaxy S26 sealed auction",
            "sourceUrl": "https://example.com/auctions/galaxy-s26",
            "seller": "Auction House",
            "currentPrice": 720000,
            "bidCount": 3,
            "currency": "KRW",
            "status": "active",
        },
    )
    list_response = client.get(f"/api/v1/products/{product['id']}/auctions")

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["productId"] == product["id"]
    assert created["currentPrice"] == 720000
    assert list_response.status_code == 200
    assert list_response.json()["items"] == [created]
    assert list_response.json()["nextCursor"] is None


def test_list_product_auctions_supports_cursor_pagination() -> None:
    client = make_test_client()
    product = create_product(client)

    created_auctions: list[dict[str, object]] = []
    for index in range(3):
        response = client.post(
            f"/api/v1/products/{product['id']}/auctions",
            json={
                "title": f"Galaxy S26 sealed auction {index}",
                "sourceUrl": f"https://example.com/auctions/galaxy-s26-{index}",
                "currentPrice": 720000 + index,
            },
        )
        assert response.status_code == 201
        created_auctions.append(response.json())

    first_page = client.get(f"/api/v1/products/{product['id']}/auctions?limit=2")
    second_page = client.get(
        f"/api/v1/products/{product['id']}/auctions?limit=2"
        f"&cursor={first_page.json()['nextCursor']}"
    )

    assert [item["id"] for item in first_page.json()["items"]] == [
        created_auctions[2]["id"],
        created_auctions[1]["id"],
    ]
    assert first_page.json()["nextCursor"] == created_auctions[1]["id"]
    assert [item["id"] for item in second_page.json()["items"]] == [
        created_auctions[0]["id"]
    ]


def test_list_limit_validation_uses_common_error_shape() -> None:
    client = make_test_client()

    response = client.get("/api/v1/products?limit=0")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_product_uses_common_error_shape() -> None:
    client = make_test_client()

    response = client.get("/api/v1/products/missing-product")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert body["error"]["message"] == "상품을 찾을 수 없습니다."
    assert body["error"]["details"] == {"productId": "missing-product"}
    assert body["error"]["traceId"].startswith("req_")
