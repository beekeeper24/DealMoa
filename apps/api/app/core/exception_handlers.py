from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import DealMoaException, ErrorCode


def make_trace_id() -> str:
    return f"req_{uuid4().hex}"


def error_response(
    *,
    code: str,
    message: str,
    details: object,
    trace_id: str,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "traceId": trace_id,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DealMoaException)
    async def dealmoa_exception_handler(
        request: Request,
        exc: DealMoaException,
    ) -> JSONResponse:
        return error_response(
            code=exc.error_code.code,
            message=exc.message,
            details=exc.details,
            trace_id=request.headers.get("X-Request-ID", make_trace_id()),
            status_code=int(exc.error_code.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        error_code = ErrorCode.VALIDATION_ERROR
        return error_response(
            code=error_code.code,
            message=error_code.default_message,
            details={"errors": exc.errors()},
            trace_id=request.headers.get("X-Request-ID", make_trace_id()),
            status_code=int(error_code.status_code),
        )
