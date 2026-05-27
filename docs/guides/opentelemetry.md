# OpenTelemetry integration

When an active OpenTelemetry span exists, LogCore automatically injects `trace_id` and `span_id` into every log record. No filter, no handler, no manual context lookup — just install the extra and it works.

## Install

```bash
pip install "logcore[otel]"
```

This pulls in `opentelemetry-api`. The integration is no-op if `opentelemetry-api` is not installed.

## Usage

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from logcore import get_logger

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("myapp")
log = get_logger("myapp", json=True)

with tracer.start_as_current_span("handle-request"):
    log.info("processing order", order_id=42)
```

Output:

```json
{
  "timestamp": "2026-05-27T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "processing order",
  "order_id": 42,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

Outside a span, the fields are simply absent — no noise for non-traced code paths.

## Compatible backends

Anything that consumes standard OTel trace/span IDs:

- Jaeger
- Zipkin
- Honeycomb
- Datadog APM
- Grafana Tempo
- AWS X-Ray (via OTel adapter)
- New Relic
- Any vendor exporting via OTLP

## With correlation IDs

OTel `trace_id` and LogCore `correlation_id` serve different layers. Use both — they're complementary:

- **Correlation ID** — your application's request-tracking concept; you control its value (e.g. `x-correlation-id` header).
- **Trace ID** — OTel's distributed trace identifier; auto-managed by the OTel SDK.

```python
with log.with_correlation_id("req-abc"):
    with tracer.start_as_current_span("handle"):
        log.info("processing")
        # Output includes both: correlation_id="req-abc" AND trace_id/span_id
```
