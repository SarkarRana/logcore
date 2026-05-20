#!/usr/bin/env python3
"""
Basic usage examples for LogCore logging library.

This script demonstrates the core features of LogCore including:
- Simple and structured logging
- JSON and text output formats
- Correlation IDs for request tracing
- Timer context managers
- Exception handling
- File logging with rotation
- Sensitive data redaction
"""

import asyncio
import tempfile
import time
from pathlib import Path

from logcore import get_logger


def basic_logging_example():
    """Demonstrate basic logging functionality."""
    print("=== Basic Logging Example ===")

    # Create a logger with human-readable output
    log = get_logger("basic_example", level="DEBUG", json=False)

    log.debug("Debug message - usually for development")
    log.info("Application started successfully")
    log.warning("This is a warning message")
    log.error("An error occurred")
    log.critical("Critical system failure!")

    print()


def structured_logging_example():
    """Demonstrate structured logging with extra fields."""
    print("=== Structured Logging Example ===")

    # Create a logger with JSON output
    log = get_logger("structured_example", level="INFO", json=True)

    # Log with additional structured data
    log.info(
        "User login", user="alice", role="admin", success=True, login_time=time.time()
    )
    log.info("Database query", table="users", query_time_ms=45.2, rows_affected=1)
    log.error(
        "Payment failed",
        user="bob",
        amount=99.99,
        currency="USD",
        error_code="INSUFFICIENT_FUNDS",
    )

    print()


def correlation_id_example():
    """Demonstrate correlation ID functionality for request tracing."""
    print("=== Correlation ID Example ===")

    log = get_logger("correlation_example", json=True)

    # Simulate processing multiple requests with correlation IDs
    def process_request(request_id):
        with log.with_correlation_id(f"req-{request_id}"):
            log.info("Request started", request_id=request_id)

            # Simulate some processing
            log.debug("Validating request data")
            time.sleep(0.1)

            log.debug("Querying database")
            time.sleep(0.05)

            log.info("Request completed", request_id=request_id, status="success")

    # Process multiple requests
    for i in range(3):
        process_request(f"abc-{i+1}")

    print()


def timer_example():
    """Demonstrate timer context manager for performance monitoring."""
    print("=== Timer Example ===")

    log = get_logger("timer_example", json=True)

    # Time a simple operation
    with log.time("data_processing", level="INFO"):
        time.sleep(0.2)  # Simulate work

    # Time with additional context
    with log.time("database_query", level="DEBUG", table="users", query_type="SELECT"):
        time.sleep(0.1)  # Simulate database query

    # Nested timing operations
    with log.time("full_request", level="INFO"):
        log.info("Starting request processing")

        with log.time("authentication", level="DEBUG"):
            time.sleep(0.05)  # Simulate auth check

        with log.time("business_logic", level="DEBUG"):
            time.sleep(0.15)  # Simulate business logic

        log.info("Request processing completed")

    print()


def exception_example():
    """Demonstrate exception logging with automatic traceback."""
    print("=== Exception Example ===")

    log = get_logger(
        "exception_example", json=False
    )  # Human-readable for better traceback display

    # Simulate various types of exceptions
    try:
        # Division by zero
        _ = 10 / 0
    except ZeroDivisionError:
        log.exception(
            "Mathematical error occurred", operation="division", dividend=10, divisor=0
        )

    try:
        # Key error
        data = {"name": "Alice", "age": 30}
        _ = data["email"]  # Key doesn't exist
    except KeyError as e:
        log.exception(
            "Missing data field",
            required_field=str(e),
            available_fields=list(data.keys()),
        )

    try:
        # Type error
        numbers = [1, 2, 3, "four", 5]
        _ = sum(numbers)  # type: ignore[arg-type]
    except TypeError:
        log.exception(
            "Data type error in calculation",
            data_types=[type(x).__name__ for x in numbers],
        )

    print()


def file_logging_example():
    """Demonstrate file logging with rotation."""
    print("=== File Logging Example ===")

    # Create a temporary directory for log files
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "app.log"

        # Create logger with file output and small file size for demonstration
        log = get_logger(
            "file_example",
            level="INFO",
            json=True,
            file=str(log_file),
            max_file_size=1024,  # 1KB for quick rotation demo
            backup_count=3,
        )

        print(f"Logging to: {log_file}")

        # Generate enough log messages to trigger rotation
        for i in range(20):
            log.info(f"Log message {i+1}", iteration=i + 1, message_size="medium")
            if i % 5 == 0:
                log.warning("Periodic warning", iteration=i + 1)

        # List all created log files
        log_files = sorted(Path(temp_dir).glob("*.log*"))
        print(f"Created {len(log_files)} log files:")
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"  {log_file.name}: {size} bytes")

    print()


def redaction_example():
    """Demonstrate sensitive data redaction."""
    print("=== Data Redaction Example ===")

    # Configure logger to redact sensitive fields
    sensitive_fields = {"password", "token", "ssn", "credit_card", "api_key"}
    log = get_logger("security_example", json=True, redact_fields=sensitive_fields)

    # Log data with sensitive fields - they should be redacted
    log.info(
        "User registration",
        username="alice",
        email="alice@example.com",
        password="super_secret_password",  # Should be redacted
        age=28,
    )

    log.info(
        "API request",
        endpoint="/api/v1/users",
        api_key="sk_live_abc123xyz789",  # Should be redacted
        user_id=12345,
        method="POST",
    )

    log.info(
        "Payment processing",
        amount=99.99,
        currency="USD",
        credit_card="4111-1111-1111-1111",  # Should be redacted
        merchant="Example Store",
    )

    print()


async def async_example():
    """Demonstrate async support with correlation IDs."""
    print("=== Async Support Example ===")

    log = get_logger("async_example", json=True)

    async def async_task(task_id, duration):
        """Simulate an async task with logging."""
        with log.with_correlation_id(f"task-{task_id}"):
            log.info("Async task started", task_id=task_id, expected_duration=duration)

            # Simulate async work
            await asyncio.sleep(duration)

            log.info("Async task completed", task_id=task_id, actual_duration=duration)

    # Run multiple async tasks concurrently
    tasks = [
        async_task(1, 0.1),
        async_task(2, 0.2),
        async_task(3, 0.15),
    ]

    await asyncio.gather(*tasks)
    print()


def environment_config_example():
    """Demonstrate environment-based configuration."""
    print("=== Environment Configuration Example ===")

    import os

    # Set environment variables (in real usage, these would be set externally)
    os.environ.update(
        {
            "LOGCORE_LEVEL": "DEBUG",
            "LOGCORE_JSON": "true",
            "LOGCORE_REDACT_FIELDS": "secret,private_key,password",
        }
    )

    # Create logger that picks up environment configuration
    log = get_logger("env_config_example")

    log.debug("Debug message (enabled via environment)")
    log.info(
        "Configuration loaded from environment",
        level_from_env=os.environ.get("LOGCORE_LEVEL"),
        json_from_env=os.environ.get("LOGCORE_JSON"),
    )

    # Test redaction from environment config
    log.info("Secret data", secret="should_be_redacted", public_data="visible")

    # Clean up environment
    for key in ["LOGCORE_LEVEL", "LOGCORE_JSON", "LOGCORE_REDACT_FIELDS"]:
        os.environ.pop(key, None)

    print()


def web_framework_simulation():
    """Simulate web framework integration patterns."""
    print("=== Web Framework Integration Simulation ===")

    log = get_logger("web_framework", json=True)

    def simulate_request(method, path, user_id=None):
        """Simulate handling a web request with proper logging."""
        import uuid

        # Generate correlation ID for the request
        correlation_id = str(uuid.uuid4())

        with log.with_correlation_id(correlation_id):
            # Log request start
            log.info("Request started", method=method, path=path, user_id=user_id)

            # Simulate request processing with timing
            with log.time("request_processing", method=method, path=path):
                # Simulate authentication
                if user_id:
                    with log.time("authentication"):
                        time.sleep(0.05)  # Auth check
                        log.info("User authenticated", user_id=user_id)

                # Simulate business logic
                with log.time("business_logic"):
                    time.sleep(0.1)  # Business processing
                    log.info("Business logic completed", path=path)

                # Simulate response
                status_code = 200 if user_id else 401
                log.info(
                    "Request completed",
                    method=method,
                    path=path,
                    status_code=status_code,
                    correlation_id=correlation_id,
                )

                return status_code

    # Simulate different types of requests
    simulate_request("GET", "/api/users", user_id="alice")
    simulate_request("POST", "/api/login")
    simulate_request("GET", "/api/users/123", user_id="bob")

    print()


def main():
    """Run all examples."""
    print("LogCore Basic Examples")
    print("=" * 50)

    # Run synchronous examples
    basic_logging_example()
    structured_logging_example()
    correlation_id_example()
    timer_example()
    exception_example()
    file_logging_example()
    redaction_example()
    environment_config_example()
    web_framework_simulation()

    # Run async example
    asyncio.run(async_example())

    print("All examples completed!")
    print("\nTry running with different environment variables:")
    print("  LOGCORE_LEVEL=DEBUG python examples/basic.py")
    print("  LOGCORE_JSON=false python examples/basic.py")


if __name__ == "__main__":
    main()
