from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response as StarletteResponse

REQUEST_COUNT = Counter(
    "dealmoa_api_http_requests_total",
    "Total API HTTP requests.",
    ("method", "path", "status_code"),
)
REQUEST_DURATION = Histogram(
    "dealmoa_api_http_request_duration_seconds",
    "API HTTP request duration in seconds.",
    ("method", "path"),
)


def register_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def record_request_metrics(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = perf_counter() - started_at
            path = route_template(request)
            method = request.method.upper()
            REQUEST_COUNT.labels(
                method=method,
                path=path,
                status_code=str(status_code),
            ).inc()
            REQUEST_DURATION.labels(method=method, path=path).observe(duration)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> StarletteResponse:
        return StarletteResponse(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        root_path = request.scope.get("root_path")
        if isinstance(root_path, str) and root_path and not path.startswith(root_path):
            return f"{root_path}{path}"
        return path
    return request.url.path
