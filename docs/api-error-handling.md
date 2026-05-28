# API Error Handling

## Goal

DealMoa uses a consistent exception and error-code policy so backend code, frontend handling, logs, and tests all speak the same language.

The design mirrors the previous COC project pattern:

```text
common base exception
  -> domain base exception
    -> concrete business exception
```

In Python, do not name the project base exception `BaseException`, because Python already has a built-in `BaseException`. Use `DealMoaException` instead.

## Response Shape

Error responses use this shape:

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "상품을 찾을 수 없습니다.",
    "details": {},
    "traceId": "req_abc123"
  }
}
```

Field meanings:

- `code`: stable error code used by frontend and tests.
- `message`: user-facing Korean message.
- `details`: structured context such as invalid fields or conflicting IDs.
- `traceId`: request/log correlation ID.

Frontend behavior should branch on `code`, not on `message`.

## Exception Hierarchy

```text
DealMoaException
  ├─ ProductException
  ├─ DealException
  ├─ AuctionException
  ├─ AuthException
  ├─ FavoriteException
  ├─ NotificationException
  ├─ ReviewException
  ├─ SubmissionException
  ├─ AdminException
  ├─ SearchException
  └─ AiAssistantException
```

Create concrete exception classes only when the business meaning is clear and reused.

Examples:

```text
ProductException
  └─ ProductNotFoundException

AuctionException
  ├─ AuctionNotFoundException
  ├─ AuctionAlreadyEndedException
  └─ BidTooLowException

FavoriteException
  ├─ FavoriteAlreadyExistsException
  └─ FavoriteNotFoundException
```

Do not create a new class for every small validation failure. Simple input errors should use Pydantic validation or a shared invalid-request exception.

## Error Code Policy

Each error code has:

- symbolic name: `PRODUCT_NOT_FOUND`
- HTTP status code: `404`
- default Korean message

Initial code groups:

```text
Common
- INVALID_REQUEST
- VALIDATION_ERROR
- INTERNAL_SERVER_ERROR

Auth
- UNAUTHORIZED
- TOKEN_EXPIRED
- INVALID_REFRESH_TOKEN
- UNSUPPORTED_OAUTH_PROVIDER
- OAUTH_PROVIDER_ERROR
- FORBIDDEN
- ADMIN_REQUIRED

Product/Deal/Auction
- PRODUCT_NOT_FOUND
- DEAL_NOT_FOUND
- AUCTION_NOT_FOUND
- AUCTION_ALREADY_ENDED
- BID_TOO_LOW

Favorite/Notification
- FAVORITE_ALREADY_EXISTS
- FAVORITE_NOT_FOUND
- NOTIFICATION_NOT_FOUND

Search/AI
- SEARCH_UNAVAILABLE
- INVALID_SEARCH_CURSOR
- AI_ASSISTANT_UNAVAILABLE

Admin/Review/Submission
- SUBMISSION_NOT_FOUND
- SUBMISSION_ALREADY_REVIEWED
- REVIEW_ALREADY_APPROVED
```

## HTTP Status Mapping

```text
400 Bad Request       invalid request or cursor
401 Unauthorized      missing/expired/invalid authentication
403 Forbidden         permission denied or admin required
404 Not Found         resource not found
409 Conflict          duplicate favorite, ended auction, low bid, already reviewed
422 Unprocessable     Pydantic validation error
429 Too Many Requests rate limit
500 Internal Error    unexpected server error
503 Unavailable       Elasticsearch, AI provider, or dependent service unavailable
```

## FastAPI Handling Rule

Application code should raise domain exceptions:

```python
raise ProductNotFoundException(product_id)
raise BidTooLowException(current_price=current_price, bid_price=bid_price)
```

Routers and use cases should not raise FastAPI `HTTPException` for business errors.

FastAPI registers global handlers for:

- `DealMoaException`
- Pydantic/FastAPI validation errors
- authentication errors
- unexpected exceptions

Unexpected exceptions must not expose stack traces or internal details in the HTTP response.

## Python Shape

```python
class DealMoaException(Exception):
    def __init__(self, error_code, message=None, details=None):
        self.error_code = error_code
        self.message = message or error_code.default_message
        self.details = details or {}
        super().__init__(self.message)
```

```python
class ProductException(DealMoaException):
    pass

class ProductNotFoundException(ProductException):
    def __init__(self, product_id: str):
        super().__init__(
            ErrorCode.PRODUCT_NOT_FOUND,
            details={"productId": product_id},
        )
```

This one extra domain layer is intentional. It makes logs, tests, and code navigation easier as the number of domains grows.
