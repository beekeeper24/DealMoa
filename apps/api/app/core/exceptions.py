from enum import Enum
from http import HTTPStatus
from typing import Any


class ErrorCode(Enum):
    PRODUCT_NOT_FOUND = (
        "PRODUCT_NOT_FOUND",
        HTTPStatus.NOT_FOUND,
        "상품을 찾을 수 없습니다.",
    )
    VALIDATION_ERROR = (
        "VALIDATION_ERROR",
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "요청 값이 올바르지 않습니다.",
    )
    INTERNAL_SERVER_ERROR = (
        "INTERNAL_SERVER_ERROR",
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "서버 오류가 발생했습니다.",
    )

    def __init__(self, code: str, status_code: HTTPStatus, default_message: str) -> None:
        self.code = code
        self.status_code = status_code
        self.default_message = default_message


class DealMoaException(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message or error_code.default_message
        self.details = details or {}
        super().__init__(self.message)


class ProductException(DealMoaException):
    pass


class ProductNotFoundException(ProductException):
    def __init__(self, product_id: str) -> None:
        super().__init__(
            ErrorCode.PRODUCT_NOT_FOUND,
            details={"productId": product_id},
        )
