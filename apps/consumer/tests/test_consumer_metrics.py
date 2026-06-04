from consumer_app.config import ConsumerSettings
from consumer_app.metrics import ConsumerMetrics
from prometheus_client import CollectorRegistry


def test_consumer_metrics_settings_default_to_enabled_port(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CONSUMER_METRICS_ENABLED", raising=False)
    monkeypatch.delenv("CONSUMER_METRICS_PORT", raising=False)

    settings = ConsumerSettings()

    assert settings.consumer_metrics_enabled is True
    assert settings.consumer_metrics_port == 9101


def test_consumer_metrics_records_event_statuses() -> None:
    metrics = ConsumerMetrics(registry=CollectorRegistry())

    metrics.record_event(
        consumer_name="search-index",
        event_type="deal.created",
        status="handled",
    )
    expected_sample = (
        'dealmoa_consumer_events_total{consumer="search-index",'
        'event_type="deal.created",status="handled"} 1.0'
    )

    assert expected_sample in metrics.generate().decode("utf-8")
