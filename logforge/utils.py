"""Utilities for LogForge."""

import asyncio
import contextvars
import time
import uuid
from contextlib import contextmanager
from typing import Any, Generator, Optional


correlation_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'correlation_id', default=None
)


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    correlation_context.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    return correlation_context.get()


@contextmanager
def correlation_id_context(correlation_id: Optional[str] = None) -> Generator[str, None, None]:
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    token = correlation_context.set(correlation_id)
    try:
        yield correlation_id
    finally:
        correlation_context.reset(token)


class Timer:
    def __init__(self, logger, operation_name: str, level: str = "INFO", **kwargs):
        self.logger = logger
        self.operation_name = operation_name
        self.level = level.upper()
        self.extra_fields = kwargs
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger._log(
            self.level,
            f"Starting {self.operation_name}",
            **self.extra_fields
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        if exc_type is not None:
            self.logger._log(
                "ERROR",
                f"Failed {self.operation_name}",
                duration_ms=round(duration * 1000, 2),
                exception=str(exc_val) if exc_val else None,
                **self.extra_fields
            )
        else:
            self.logger._log(
                self.level,
                f"Completed {self.operation_name}",
                duration_ms=round(duration * 1000, 2),
                **self.extra_fields
            )
    
    @property
    def elapsed(self) -> Optional[float]:
        if self.start_time is None:
            return None
        
        end_time = self.end_time or time.perf_counter()
        return end_time - self.start_time


class AsyncTimer:
    def __init__(self, logger, operation_name: str, level: str = "INFO", **kwargs):
        self.logger = logger
        self.operation_name = operation_name
        self.level = level.upper()
        self.extra_fields = kwargs
        self.start_time = None
        self.end_time = None
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        self.logger._log(
            self.level,
            f"Starting {self.operation_name}",
            **self.extra_fields
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        if exc_type is not None:
            self.logger._log(
                "ERROR",
                f"Failed {self.operation_name}",
                duration_ms=round(duration * 1000, 2),
                exception=str(exc_val) if exc_val else None,
                **self.extra_fields
            )
        else:
            self.logger._log(
                self.level,
                f"Completed {self.operation_name}",
                duration_ms=round(duration * 1000, 2),
                **self.extra_fields
            )
    
    @property
    def elapsed(self) -> Optional[float]:
        if self.start_time is None:
            return None
        
        end_time = self.end_time or time.perf_counter()
        return end_time - self.start_time


def is_async_context() -> bool:
    try:
        asyncio.current_task()
        return True
    except RuntimeError:
        return False


def safe_str(obj: Any, max_length: int = 1000) -> str:
    try:
        text = str(obj)
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    except Exception:
        return f"<{type(obj).__name__} object>"
