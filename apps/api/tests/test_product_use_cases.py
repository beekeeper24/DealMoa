from typing import cast

import pytest
from app.core.exceptions import InvalidSearchCursorException, ProductNotFoundException
from app.modules.products.repository import ProductRepository
from app.modules.products.use_cases import ProductUseCases


class EmptyProductRepository:
    def get_product(self, product_id: str) -> None:
        return None


class CursorRejectingRepository:
    def get_product(self, product_id: str) -> None:
        return None

    def list_products(self, *, limit: int, cursor: str | None) -> object:
        raise InvalidSearchCursorException(cursor or "")


def test_get_product_raises_domain_exception_for_missing_product() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, EmptyProductRepository()))

    with pytest.raises(ProductNotFoundException) as exc_info:
        use_cases.get_product("missing-product")

    assert exc_info.value.error_code.code == "PRODUCT_NOT_FOUND"
    assert exc_info.value.details == {"productId": "missing-product"}


def test_list_products_raises_domain_exception_for_invalid_cursor() -> None:
    use_cases = ProductUseCases(cast(ProductRepository, CursorRejectingRepository()))

    with pytest.raises(InvalidSearchCursorException) as exc_info:
        use_cases.list_products(limit=20, cursor="bad-cursor")

    assert exc_info.value.error_code.code == "INVALID_SEARCH_CURSOR"
    assert exc_info.value.details == {"cursor": "bad-cursor"}
