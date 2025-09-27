# LogForge Project Structure

This document provides an overview of the LogForge project structure and implementation.

## Project Overview

LogForge is a production-ready logging library for Python that provides:

- Simple API with single entrypoint
- Structured JSON and human-readable logging
- Built-in correlation IDs for distributed tracing
- Performance timing with context managers
- Automatic sensitive data redaction
- File logging with rotation
- Async support
- Thread-safety
- Environment-based configuration

## File Structure

```
logforge/
├── __init__.py                 # Package initialization and public API
├── config.py                   # Configuration management
├── formatters.py               # JSON and text formatters with redaction
├── handlers.py                 # Console and file handlers
├── logger.py                   # Main logger implementation
├── utils.py                    # Utilities (correlation IDs, timers)
├── py.typed                    # Type hints marker
│
├── tests/
│   ├── __init__.py
│   ├── pytest.ini
│   └── test_logforge.py        # Comprehensive test suite
│
├── examples/
│   ├── basic.py                # Basic usage examples
│   ├── flask_example.py        # Flask web framework integration
│   └── microservice_example.py # Microservice architecture demo
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI/CD pipeline
│       └── release.yml         # Release workflow
│
├── pyproject.toml              # Package configuration
├── README.md                   # Main documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT license
├── .gitignore                  # Git ignore rules
└── .pre-commit-config.yaml     # Pre-commit hooks
```

## Core Components

### 1. Configuration (`config.py`)

- `LogLevel` enum for log levels
- `LogCoreConfig` dataclass for configuration
- Environment variable support
- Default sensitive field redaction

### 2. Formatters (`formatters.py`)

- `JSONFormatter`: Structured JSON output
- `TextFormatter`: Human-readable colored output
- `RedactingFormatter`: Base class with sensitive data redaction
- Automatic timestamp formatting
- Exception traceback formatting

### 3. Handlers (`handlers.py`)

- `ConsoleHandler`: Console output
- `FileHandler`: File output with rotation
- Automatic directory creation
- Configurable file sizes and backup counts

### 4. Utilities (`utils.py`)

- Correlation ID generation and context management
- `Timer` and `AsyncTimer` context managers
- Thread-safe correlation ID storage
- Safe string conversion utilities

### 5. Main Logger (`logger.py`)

- `LogForgeLogger` class with full logging API
- Thread-safe logger caching
- Integration with Python's standard logging
- Support for all log levels (debug, info, warning, error, critical)
- Built-in exception logging

## Key Features Implementation

### Structured Logging

```python
log.info("User action", user="alice", action="login", success=True)
```

### Correlation IDs

```python
with log.with_correlation_id("req-123"):
    log.info("Processing request")
```

### Performance Timing

```python
with log.time("database_query"):
    result = database.query()
```

### Exception Handling

```python
try:
    risky_operation()
except Exception:
    log.exception("Operation failed")
```

### Sensitive Data Redaction

```python
log = get_logger("app", redact_fields={"password", "token"})
log.info("Login", username="alice", password="secret123")  # password redacted
```

## Testing

Comprehensive test suite covers:

- Configuration from code and environment
- JSON and text formatting
- Sensitive data redaction
- File logging with rotation
- Correlation ID functionality
- Timer context managers
- Exception logging
- Thread safety
- Async support

## Examples

### Basic Usage (`examples/basic.py`)

Demonstrates all core features with simple examples.

### Flask Integration (`examples/flask_example.py`)

Shows web framework integration with:

- Request/response logging
- Correlation ID propagation
- Error handling
- Performance monitoring

### Microservice Architecture (`examples/microservice_example.py`)

Simulates distributed system logging with:

- Service-to-service communication
- Distributed tracing
- Business metrics logging
- Load testing simulation

## CI/CD

GitHub Actions workflows provide:

- Multi-version Python testing (3.8-3.12)
- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit, safety)
- Automated PyPI publishing
- Coverage reporting

## Installation & Usage

```bash
# Install
pip install logforge

# Optional color support
pip install logforge[colors]

# Basic usage
from logforge import get_logger
log = get_logger("myapp", level="INFO", json=True)
log.info("Hello LogForge!", user="test")
```

## Production Readiness

LogForge is designed for production use with:

✅ **Performance**: Minimal overhead, lazy formatting  
✅ **Security**: Automatic sensitive data redaction  
✅ **Reliability**: Thread-safe, exception handling  
✅ **Observability**: Structured logging, correlation IDs  
✅ **Scalability**: File rotation, async support  
✅ **Maintainability**: Comprehensive tests, type hints  
✅ **Standards**: Follows Python logging best practices

The library provides a drop-in replacement for Python's built-in logging while adding modern features needed for production applications and microservices.
