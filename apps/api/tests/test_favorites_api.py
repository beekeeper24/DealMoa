from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.pagination import CursorPage
from app.main import create_app
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser
from app.modules.favorites.router import get_favorites_use_cases
from app.modules.favorites.schemas import ProductFavoriteResponse
from fastapi.testclient import TestClient

NOW = datetime(2026, 5, 28, tzinfo=UTC)


@dataclass
class FakeAuthUseCases:
    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise AssertionError("unexpected access token")
        return AuthenticatedUser(
            id="user-1",
            email="user@example.com",
            nickname="Deal User",
            role="USER",
        )


@dataclass
class FakeFavoritesUseCases:
    added_product: tuple[str, str] | None = None
    removed_product: tuple[str, str] | None = None

    def add_product_favorite(self, *, user_id: str, product_id: str) -> ProductFavoriteResponse:
        self.added_product = (user_id, product_id)
        return ProductFavoriteResponse(
            id="favorite-1",
            productId=product_id,
            createdAt=NOW,
        )

    def remove_product_favorite(self, *, user_id: str, product_id: str) -> None:
        self.removed_product = (user_id, product_id)

    def list_product_favorites(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ProductFavoriteResponse]:
        return CursorPage(
            items=[
                ProductFavoriteResponse(
                    id="favorite-1",
                    productId="product-1",
                    createdAt=NOW,
                )
            ],
            next_cursor=None,
        )


def make_client(use_cases: FakeFavoritesUseCases) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_use_cases] = lambda: FakeAuthUseCases()
    app.dependency_overrides[get_favorites_use_cases] = lambda: use_cases
    return TestClient(app)


def test_add_product_favorite_requires_bearer_token() -> None:
    client = make_client(FakeFavoritesUseCases())

    response = client.put("/api/v1/me/favorites/products/product-1")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_add_product_favorite_uses_current_user() -> None:
    use_cases = FakeFavoritesUseCases()
    client = make_client(use_cases)

    response = client.put(
        "/api/v1/me/favorites/products/product-1",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json()["productId"] == "product-1"
    assert use_cases.added_product == ("user-1", "product-1")


def test_remove_product_favorite_uses_current_user() -> None:
    use_cases = FakeFavoritesUseCases()
    client = make_client(use_cases)

    response = client.delete(
        "/api/v1/me/favorites/products/product-1",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert use_cases.removed_product == ("user-1", "product-1")


def test_list_product_favorites_uses_current_user() -> None:
    client = make_client(FakeFavoritesUseCases())

    response = client.get(
        "/api/v1/me/favorites/products",
        headers={"Authorization": "Bearer access-1"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "favorite-1",
                "productId": "product-1",
                "createdAt": "2026-05-28T00:00:00Z",
            }
        ],
        "nextCursor": None,
    }
