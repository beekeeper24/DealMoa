from enum import Enum
from http import HTTPStatus
from typing import Any


class ErrorCode(Enum):
    PRODUCT_NOT_FOUND = (
        "PRODUCT_NOT_FOUND",
        HTTPStatus.NOT_FOUND,
        "상품을 찾을 수 없습니다.",
    )
    DEAL_NOT_FOUND = (
        "DEAL_NOT_FOUND",
        HTTPStatus.NOT_FOUND,
        "핫딜을 찾을 수 없습니다.",
    )
    AUCTION_NOT_FOUND = (
        "AUCTION_NOT_FOUND",
        HTTPStatus.NOT_FOUND,
        "경매를 찾을 수 없습니다.",
    )
    AUCTION_ALREADY_ENDED = (
        "AUCTION_ALREADY_ENDED",
        HTTPStatus.CONFLICT,
        "종료된 경매입니다.",
    )
    BID_TOO_LOW = (
        "BID_TOO_LOW",
        HTTPStatus.CONFLICT,
        "현재가보다 높은 금액으로 입찰해야 합니다.",
    )
    UNAUTHORIZED = (
        "UNAUTHORIZED",
        HTTPStatus.UNAUTHORIZED,
        "로그인이 필요합니다.",
    )
    TOKEN_EXPIRED = (
        "TOKEN_EXPIRED",
        HTTPStatus.UNAUTHORIZED,
        "토큰이 만료되었습니다.",
    )
    INVALID_REFRESH_TOKEN = (
        "INVALID_REFRESH_TOKEN",
        HTTPStatus.UNAUTHORIZED,
        "리프레시 토큰이 올바르지 않습니다.",
    )
    UNSUPPORTED_OAUTH_PROVIDER = (
        "UNSUPPORTED_OAUTH_PROVIDER",
        HTTPStatus.BAD_REQUEST,
        "지원하지 않는 OAuth 제공자입니다.",
    )
    OAUTH_PROVIDER_ERROR = (
        "OAUTH_PROVIDER_ERROR",
        HTTPStatus.BAD_GATEWAY,
        "OAuth 제공자 인증에 실패했습니다.",
    )
    INVALID_SEARCH_CURSOR = (
        "INVALID_SEARCH_CURSOR",
        HTTPStatus.BAD_REQUEST,
        "목록 커서가 올바르지 않습니다.",
    )
    SEARCH_UNAVAILABLE = (
        "SEARCH_UNAVAILABLE",
        HTTPStatus.SERVICE_UNAVAILABLE,
        "검색 서비스를 사용할 수 없습니다.",
    )
    NOTIFICATION_NOT_FOUND = (
        "NOTIFICATION_NOT_FOUND",
        HTTPStatus.NOT_FOUND,
        "알림을 찾을 수 없습니다.",
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


class DealException(DealMoaException):
    pass


class DealNotFoundException(DealException):
    def __init__(self, deal_id: str) -> None:
        super().__init__(
            ErrorCode.DEAL_NOT_FOUND,
            details={"dealId": deal_id},
        )


class AuctionException(DealMoaException):
    pass


class AuctionNotFoundException(AuctionException):
    def __init__(self, auction_id: str) -> None:
        super().__init__(
            ErrorCode.AUCTION_NOT_FOUND,
            details={"auctionId": auction_id},
        )


class AuctionAlreadyEndedException(AuctionException):
    def __init__(
        self,
        *,
        auction_id: str,
        status: str,
        ends_at: str | None,
    ) -> None:
        super().__init__(
            ErrorCode.AUCTION_ALREADY_ENDED,
            details={
                "auctionId": auction_id,
                "status": status,
                "endsAt": ends_at,
            },
        )


class BidTooLowException(AuctionException):
    def __init__(self, *, auction_id: str, current_price: int, bid_amount: int) -> None:
        super().__init__(
            ErrorCode.BID_TOO_LOW,
            details={
                "auctionId": auction_id,
                "currentPrice": current_price,
                "bidAmount": bid_amount,
            },
        )


class AuthException(DealMoaException):
    pass


class UnauthorizedException(AuthException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.UNAUTHORIZED)


class TokenExpiredException(AuthException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.TOKEN_EXPIRED)


class InvalidRefreshTokenException(AuthException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.INVALID_REFRESH_TOKEN)


class UnsupportedOAuthProviderException(AuthException):
    def __init__(self, provider: str) -> None:
        super().__init__(
            ErrorCode.UNSUPPORTED_OAUTH_PROVIDER,
            details={"provider": provider},
        )


class OAuthProviderException(AuthException):
    def __init__(self, provider: str) -> None:
        super().__init__(
            ErrorCode.OAUTH_PROVIDER_ERROR,
            details={"provider": provider},
        )


class InvalidSearchCursorException(DealMoaException):
    def __init__(self, cursor: str) -> None:
        super().__init__(
            ErrorCode.INVALID_SEARCH_CURSOR,
            details={"cursor": cursor},
        )


class SearchException(DealMoaException):
    pass


class SearchUnavailableException(SearchException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.SEARCH_UNAVAILABLE)


class NotificationException(DealMoaException):
    pass


class NotificationNotFoundException(NotificationException):
    def __init__(self, notification_id: str) -> None:
        super().__init__(
            ErrorCode.NOTIFICATION_NOT_FOUND,
            details={"notificationId": notification_id},
        )
