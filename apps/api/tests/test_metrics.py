from collections.abc import Iterator

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.products import models as product_models  # noqa: F401
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
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


def test_metrics_endpoint_returns_prometheus_text() -> None:
    client = make_test_client()

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "dealmoa_api_http_requests_total" in response.text
    assert "dealmoa_api_http_request_duration_seconds" in response.text


def test_metrics_records_request_counts_and_status_codes() -> None:
    client = make_test_client()

    client.get("/health")
    client.get("/api/v1/health")
    client.get("/missing-route")
    response = client.get("/metrics")

    assert metrics_has_sample(
        response.text,
        "dealmoa_api_http_requests_total",
        {
            "method": "GET",
            "path": "/health",
            "status_code": "200",
        },
    )
    assert metrics_has_sample(
        response.text,
        "dealmoa_api_http_requests_total",
        {
            "method": "GET",
            "path": "/api/v1/health",
            "status_code": "200",
        },
    )
    assert metrics_has_sample(
        response.text,
        "dealmoa_api_http_requests_total",
        {
            "method": "GET",
            "path": "/missing-route",
            "status_code": "404",
        },
    )


def test_metrics_uses_route_templates_for_dynamic_paths() -> None:
    client = make_test_client()

    client.get("/api/v1/products/missing-product")
    response = client.get("/metrics")

    assert metrics_has_sample(
        response.text,
        "dealmoa_api_http_requests_total",
        {
            "method": "GET",
            "path": "/api/v1/products/{product_id}",
            "status_code": "404",
        },
    )
    assert 'path="/api/v1/products/missing-product"' not in response.text


def test_metrics_endpoint_is_excluded_from_request_metrics() -> None:
    client = make_test_client()

    client.get("/metrics")
    response = client.get("/metrics")

    assert 'path="/metrics"' not in response.text


def test_metrics_endpoint_can_be_disabled(monkeypatch: MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("API_METRICS_ENABLED", "false")
    try:
        client = make_test_client()

        response = client.get("/metrics")

        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


def metrics_has_sample(text: str, metric_name: str, labels: dict[str, str]) -> bool:
    expected_labels = ",".join(f'{key}="{value}"' for key, value in labels.items())
    prefix = f"{metric_name}{{{expected_labels}}}"
    return any(line.startswith(prefix) for line in text.splitlines())
