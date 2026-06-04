from prometheus_client import CollectorRegistry, Counter, generate_latest, start_http_server


class ConsumerMetrics:
    def __init__(self, *, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.events_total = Counter(
            "dealmoa_consumer_events_total",
            "Total domain events processed by DealMoa consumers.",
            ["consumer", "event_type", "status"],
            registry=self.registry,
        )

    def record_event(self, *, consumer_name: str, event_type: str, status: str) -> None:
        self.events_total.labels(
            consumer=consumer_name,
            event_type=event_type,
            status=status,
        ).inc()

    def generate(self) -> bytes:
        return generate_latest(self.registry)


consumer_metrics = ConsumerMetrics()
_metrics_server_started = False


def record_consumer_event(*, consumer_name: str, event_type: str, status: str) -> None:
    consumer_metrics.record_event(
        consumer_name=consumer_name,
        event_type=event_type,
        status=status,
    )


def generate_consumer_metrics() -> bytes:
    return consumer_metrics.generate()


def start_consumer_metrics_server(*, enabled: bool, port: int) -> None:
    global _metrics_server_started
    if not enabled or _metrics_server_started:
        return
    start_http_server(port, registry=consumer_metrics.registry)
    _metrics_server_started = True
