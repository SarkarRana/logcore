# LogCore 🔥

[![PyPI version](https://badge.fury.io/py/logcore.svg)](https://badge.fury.io/py/logcore)
[![Python versions](https://img.shields.io/pypi/pyversions/logcore.svg)](https://pypi.org/project/logcore/)
[![CI](https://github.com/SarkarRana/logcore/actions/workflows/ci.yml/badge.svg)](https://github.com/SarkarRana/logcore/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/SarkarRana/logcore/blob/main/LICENSE)

**A production-ready logging library for Python**

LogCore provides a simple, structured, and extensible logging solution that works seamlessly for both small scripts and large microservices. It's designed as a drop-in alternative to Python's built-in logging with a focus on developer experience, observability, and production readiness.

## ✨ Features

- **🚀 Simple API**: Single entrypoint with intuitive configuration
- **📊 Structured Logging**: JSON and human-readable output formats
- **🔗 Correlation IDs**: Built-in request tracing support
- **⏱️ Built-in Timing**: Context managers for performance monitoring
- **🛡️ Security**: Automatic redaction of sensitive fields
- **📁 File Rotation**: Configurable log rotation and archival
- **🎨 Colorized Output**: Beautiful console logging with colors
- **⚡ Async Support**: Safe for asyncio applications
- **🧵 Thread-safe**: Concurrent logging without issues
- **🌍 Environment Configuration**: Configure via environment variables

## 🚀 Quick Start

### Installation

```bash
pip install logcore
```

For colored output support:

```bash
pip install logcore[colors]
```

### Basic Usage

```python
from logcore import get_logger

# Create a logger
log = get_logger("myapp", level="INFO", json=True)

# Simple logging
log.info("Application started")
log.error("Something went wrong")

# Structured logging with extra fields
log.info("User login", user="alice", role="admin", success=True)

# Exception logging with automatic traceback
try:
    1 / 0
except Exception:
    log.exception("Division failed")
```

## 📖 Documentation

### Configuration Options

LogCore can be configured through code or environment variables:

```python
from logcore import get_logger

log = get_logger(
    name="myapp",              # Logger name
    level="INFO",              # DEBUG, INFO, WARNING, ERROR, CRITICAL
    json=True,                 # JSON output (False for human-readable)
    file="/path/to/app.log",   # Optional file logging
    correlation_id="req-123",  # Optional correlation ID
    max_file_size=10*1024*1024, # 10MB file size limit
    backup_count=5,            # Keep 5 backup files
    redact_fields={"password", "secret"}  # Fields to redact
)
```

Calling `get_logger` with the same name a second time and no extra arguments returns the cached instance. Passing configuration arguments when a logger already exists replaces it and emits a `UserWarning` — existing references to the old logger will stop receiving records.

### Public API

```python
from logcore import get_logger, LogLevel, set_correlation_id, get_correlation_id
```

| Symbol | Description |
|---|---|
| `get_logger(name, ...)` | Create or retrieve a logger |
| `LogLevel` | Enum of valid log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `set_correlation_id(id)` | Set a correlation ID on the current context (thread/task) without a logger instance |
| `get_correlation_id()` | Read the current correlation ID, or `None` if unset |

`set_correlation_id` and `get_correlation_id` are useful in middleware that sets the ID before a logger is available:

```python
from logcore import set_correlation_id, get_correlation_id

# In ASGI/WSGI middleware, before any logger is called:
set_correlation_id(request.headers.get("x-correlation-id"))
```

### Environment Variables

Set configuration via environment variables:

```bash
export LOGCORE_LEVEL=DEBUG
export LOGCORE_JSON=true
export LOGCORE_FILE=/var/log/app.log
export LOGCORE_CORRELATION_ID=req-abc-123
export LOGCORE_REDACT_FIELDS=password,token,secret
```

### Output Formats

#### JSON Format

```json
{
  "timestamp": "2025-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "myapp",
  "message": "User login",
  "correlation_id": "req-123",
  "user": "alice",
  "success": true
}
```

#### Human-Readable Format

```
2025-01-15 10:30:45.123 INFO     myapp [cid=req-123]: User login user=alice success=true
```

### Advanced Features

#### Correlation IDs for Request Tracing

```python
from logcore import get_logger

log = get_logger("api")

# Set correlation ID for the entire request context
with log.with_correlation_id("req-abc-123"):
    log.info("Processing request")
    process_request()
    log.info("Request completed")
```

#### Performance Timing

```python
# Measure execution time automatically
with log.time("database_query", level="DEBUG"):
    result = expensive_database_operation()

# Outputs:
# Starting database_query
# Completed database_query duration_ms=234.56
```

#### Exception Handling

```python
try:
    risky_operation()
except Exception as e:
    log.exception("Operation failed", operation="risky_operation", user_id=123)
    # Automatically includes full traceback
```

#### Sensitive Data Redaction

Fields are **partially masked** — enough to confirm a value was present without leaking it:

```python
log = get_logger("secure", redact_fields={"password", "token", "ssn"})

log.info("User data", username="alice", password="secret123", token="abc123", role="admin")
# Output: ... username=alice password=se*** token=a*** role=admin
```

Values of 4 characters or fewer are fully redacted (`[REDACTED]`). Longer values reveal a short prefix so you can correlate log lines without exposing the secret.

Default redacted fields: `password`, `passwd`, `secret`, `token`, `key`, `api_key`, `access_token`, `auth`, `authorization`, `credential`, `private_key`, `cert`, `certificate`.

#### OpenTelemetry Integration

When an active [OpenTelemetry](https://opentelemetry.io/) span exists, LogCore automatically injects `trace_id` and `span_id` into every log record — zero configuration required.

```bash
pip install logcore[otel]
```

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from logcore import get_logger

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("myapp")
log = get_logger("myapp", json=True)

with tracer.start_as_current_span("handle-request"):
    log.info("Processing order", order_id=42)
    # {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    #  "span_id": "00f067aa0ba902b7", "message": "Processing order", ...}
```

Outside a span the fields are simply absent — no noise in non-traced code paths. Works with any OTel-compatible backend (Jaeger, Zipkin, Honeycomb, Datadog, etc.).

#### File Logging with Rotation

```python
log = get_logger(
    "myapp",
    file="/var/log/myapp.log",
    max_file_size=10 * 1024 * 1024,  # 10MB
    backup_count=5                    # Keep 5 old files
)
```

Files are automatically rotated:

- `myapp.log` (current)
- `myapp.log.1` (previous)
- `myapp.log.2` (older)
- etc.

### Async Support

LogCore is fully compatible with asyncio:

```python
import asyncio
from logcore import get_logger

async def main():
    log = get_logger("async_app")

    # Correlation IDs work across await boundaries
    with log.with_correlation_id():
        log.info("Starting async operation")
        await some_async_task()
        log.info("Async operation completed")

    # Async timing context manager
    async with log.time("async_operation"):
        await another_async_task()

asyncio.run(main())
```

### Integration with Web Frameworks

#### Flask Example

```python
from flask import Flask, request, g
from logcore import get_logger
import uuid

app = Flask(__name__)
log = get_logger("webapp")

@app.before_request
def before_request():
    g.correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))

@app.after_request
def after_request(response):
    with log.with_correlation_id(g.correlation_id):
        log.info(
            "Request completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=...  # Add timing logic
        )
    return response

@app.route('/users/<user_id>')
def get_user(user_id):
    with log.with_correlation_id(g.correlation_id):
        log.info("Fetching user", user_id=user_id)
        # ... your logic here
```

#### FastAPI Example

```python
from fastapi import FastAPI, Request
from logcore import get_logger
import time
import uuid

app = FastAPI()
log = get_logger("api")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    start_time = time.time()

    with log.with_correlation_id(correlation_id):
        log.info("Request started", method=request.method, url=str(request.url))

        response = await call_next(request)

        duration = (time.time() - start_time) * 1000
        log.info(
            "Request completed",
            status_code=response.status_code,
            duration_ms=round(duration, 2)
        )

    response.headers["x-correlation-id"] = correlation_id
    return response
```

## ⚡ Performance

Measured on Python 3.12, Apple M-series, writing to `/dev/null` (I/O excluded):

| Mode | µs / call | Notes |
|---|---|---|
| stdlib `logging` (text) | ~6 µs | baseline |
| stdlib + manual JSON formatter | ~7 µs | +1 µs |
| **LogCore JSON** | **~13 µs** | +7 µs for structured output |
| LogCore text (colored) | ~36 µs | +30 µs for strftime + color |

JSON mode is the recommended default for production — it costs ~7 µs per call over stdlib and produces machine-readable output that log aggregators can query directly.

Run the benchmark yourself: `python examples/benchmark.py`

## 🆚 Comparison with Other Libraries

### vs. Built-in `logging`

| Feature            | LogCore                   | Built-in logging             |
| ------------------ | ------------------------- | ---------------------------- |
| Setup complexity   | ⭐⭐⭐⭐⭐ Single line    | ⭐⭐ Complex setup           |
| Structured logging | ⭐⭐⭐⭐⭐ Built-in       | ⭐⭐ Manual implementation   |
| JSON output        | ⭐⭐⭐⭐⭐ Automatic      | ⭐⭐ Custom formatter needed |
| Correlation IDs    | ⭐⭐⭐⭐⭐ Built-in       | ⭐ Custom context needed     |
| Security           | ⭐⭐⭐⭐⭐ Auto-redaction | ⭐ Manual filtering          |
| Colors             | ⭐⭐⭐⭐⭐ Auto-detected  | ⭐⭐ Third-party needed      |

### vs. `loguru`

| Feature          | LogCore                     | Loguru                         |
| ---------------- | --------------------------- | ------------------------------ |
| Production focus | ⭐⭐⭐⭐⭐ Enterprise-ready | ⭐⭐⭐⭐ Great for development |
| Correlation IDs  | ⭐⭐⭐⭐⭐ Built-in context | ⭐⭐ Manual binding            |
| Security         | ⭐⭐⭐⭐⭐ Auto-redaction   | ⭐⭐ Manual filtering          |
| Async support    | ⭐⭐⭐⭐⭐ Context-aware    | ⭐⭐⭐ Basic support           |
| Performance      | ⭐⭐⭐⭐ Good               | ⭐⭐⭐⭐⭐ Excellent           |
| Ecosystem        | ⭐⭐⭐⭐⭐ Standard logging | ⭐⭐⭐ Custom approach         |

## 🛠️ Development

### Setup

```bash
git clone https://github.com/SarkarRana/logcore.git
cd logcore

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=logcore

# Run specific test categories
pytest -m "not slow"          # Skip slow tests
pytest -m integration         # Run integration tests only
```

### Code Quality

```bash
# Format code
black logcore tests
isort logcore tests

# Lint
flake8 logcore tests

# Type checking
mypy logcore
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🎯 Roadmap

### Shipped
- [x] **OpenTelemetry**: Automatic trace/span ID injection from active spans (v0.1.4)
- [x] **Async support**: `AsyncTimer` with isolated correlation IDs per task (v0.1.4)
- [x] **Partial masking**: Secrets show a short prefix, not just `[REDACTED]` (v0.1.4)
- [x] **Accurate caller info**: `filename`, `lineno`, and `funcName` now reflect the real call site (v0.1.5)
- [x] **Reconfiguration warning**: `get_logger` emits `UserWarning` when replacing a cached logger (v0.1.5)
- [x] **`LogLevel`, `set_correlation_id`, `get_correlation_id`** promoted to top-level public API (v0.1.5)

### Planned
- [ ] **Sentry integration**: Automatic error forwarding with structured context
- [ ] **Log sampling**: Rate-based sampling to protect downstream systems under load
- [ ] **Async batching**: Buffer and flush writes for lower-latency hot paths
- [ ] **OTLP export**: Direct log shipping to OpenTelemetry collectors
- [ ] **Kubernetes metadata**: Pod/node/namespace injection via downward API env vars

## 💖 Support

If you find LogCore useful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 📖 Improving documentation
- 💻 Contributing code

---

**Built with ❤️ for the Python community**
