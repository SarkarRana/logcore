# Quickstart

This page gets you from `pip install` to structured production logs in five minutes.

## Install

```bash
pip install logcore
```

## A logger in two lines

```python
from logcore import get_logger

log = get_logger("myapp")
log.info("Application started")
```

You get colored human-readable output on stderr by default. For machine-readable JSON:

```python
log = get_logger("myapp", json=True)
log.info("user login", user="alice", role="admin", success=True)
```

```json
{
  "timestamp": "2026-05-27T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "myapp",
  "message": "user login",
  "user": "alice",
  "role": "admin",
  "success": true
}
```

## Configuration

Either pass arguments to `get_logger`:

```python
log = get_logger(
    name="myapp",
    level="INFO",                          # DEBUG, INFO, WARNING, ERROR, CRITICAL
    json=True,
    file="/var/log/myapp.log",
    max_file_size=10 * 1024 * 1024,        # 10 MB
    backup_count=5,
    redact_fields={"password", "secret"},
)
```

Or set environment variables:

```bash
export LOGCORE_LEVEL=DEBUG
export LOGCORE_JSON=true
export LOGCORE_FILE=/var/log/myapp.log
export LOGCORE_REDACT_FIELDS=password,token,secret
```

See the [configuration reference](configuration.md) for the full list of options.

## Five things you'll actually use

### 1. Structured fields

Pass any keyword arguments — they become first-class fields in the log record:

```python
log.info("order placed", order_id=42, amount=99.99, currency="USD")
```

### 2. Exception logging with traceback

```python
try:
    risky_operation()
except Exception:
    log.exception("operation failed", operation="risky_operation")
    # Includes the full traceback automatically.
```

### 3. Operation timing

```python
with log.time("database_query"):
    result = run_query()
# Emits: "Starting database_query" then "Completed database_query duration_ms=234.56"
```

Works the same way in async code with `async with log.time(...)` — auto-detected.

### 4. Correlation IDs for request tracing

```python
with log.with_correlation_id("req-abc"):
    log.info("processing")
    do_work()
    log.info("done")
# Every record under this block carries cid=req-abc.
```

See [correlation IDs](guides/correlation_ids.md) for async, middleware, and cross-task patterns.

### 5. Sensitive data redaction (automatic)

```python
log.info("user data", username="alice", password="hunter2-very-long")
# Output: ... username=alice password=hu*** ...
```

Default redacted fields: `password`, `secret`, `token`, `key`, `api_key`, `auth`, etc. Customize via `redact_fields=`.

## What's next

- [**Log sampling**](guides/sampling.md) — drop noisy records while keeping every line from failed requests
- [**Correlation IDs**](guides/correlation_ids.md) — request scoping for sync, async, and middleware
- [**Framework integrations**](guides/frameworks.md) — Flask and FastAPI middleware examples
- [**OpenTelemetry**](guides/opentelemetry.md) — automatic trace/span ID injection
