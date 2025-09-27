# LogForge 🔥

[![PyPI version](https://badge.fury.io/py/logcore.svg)](https://badge.fury.io/py/logcore)
[![Python versions](https://img.shields.io/pypi/pyversions/logcore.svg)](https://pypi.org/project/logcore/)
[![CI](https://github.com/SarkarRana/logforge/actions/workflows/ci.yml/badge.svg)](https://github.com/SarkarRana/logforge/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/SarkarRana/logforge/blob/main/LICENSE)

**A production-ready logging library for Python**

LogForge provides a simple, structured, and extensible logging solution that works seamlessly for both small scripts and large microservices. It's designed as a drop-in alternative to Python's built-in logging with a focus on developer experience, observability, and production readiness.

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
pip install logforge[colors]
```

### Basic Usage

```python
from logforge import get_logger

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

LogForge can be configured through code or environment variables:

```python
from logforge import get_logger

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

### Environment Variables

Set configuration via environment variables:

```bash
export LOGFORGE_LEVEL=DEBUG
export LOGFORGE_JSON=true
export LOGFORGE_FILE=/var/log/app.log
export LOGFORGE_CORRELATION_ID=req-abc-123
export LOGFORGE_REDACT_FIELDS=password,token,secret
```

### Output Formats

#### JSON Format

```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
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
from logforge import get_logger

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

```python
# Configure fields to automatically redact
log = get_logger("secure", redact_fields={"password", "token", "ssn"})

log.info("User data", username="alice", password="secret123", role="admin")
# Output: ... username=alice password=[REDACTED] role=admin
```

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

LogForge is fully compatible with asyncio:

```python
import asyncio
from logforge import get_logger

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
from logforge import get_logger
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
from logforge import get_logger
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

## 🆚 Comparison with Other Libraries

### vs. Built-in `logging`

| Feature            | LogForge                  | Built-in logging             |
| ------------------ | ------------------------- | ---------------------------- |
| Setup complexity   | ⭐⭐⭐⭐⭐ Single line    | ⭐⭐ Complex setup           |
| Structured logging | ⭐⭐⭐⭐⭐ Built-in       | ⭐⭐ Manual implementation   |
| JSON output        | ⭐⭐⭐⭐⭐ Automatic      | ⭐⭐ Custom formatter needed |
| Correlation IDs    | ⭐⭐⭐⭐⭐ Built-in       | ⭐ Custom context needed     |
| Security           | ⭐⭐⭐⭐⭐ Auto-redaction | ⭐ Manual filtering          |
| Colors             | ⭐⭐⭐⭐⭐ Auto-detected  | ⭐⭐ Third-party needed      |

### vs. `loguru`

| Feature          | LogForge                    | Loguru                         |
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
git clone https://github.com/logforge/logforge.git
cd logforge

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
pytest --cov=logforge

# Run specific test categories
pytest -m "not slow"          # Skip slow tests
pytest -m integration         # Run integration tests only
```

### Code Quality

```bash
# Format code
black logforge tests
isort logforge tests

# Lint
flake8 logforge tests

# Type checking
mypy logforge
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🎯 Roadmap

- [ ] **Performance Optimizations**: Async batching, lazy formatting
- [ ] **Integrations**: OpenTelemetry, Sentry, DataDog
- [ ] **Advanced Features**: Log sampling, rate limiting
- [ ] **Cloud Native**: Kubernetes-friendly output formats
- [ ] **Monitoring**: Health checks and metrics endpoints

## 💖 Support

If you find LogForge useful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 📖 Improving documentation
- 💻 Contributing code

---

**Built with ❤️ for the Python community**
