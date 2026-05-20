"""Core logging functionality for LogCore."""

import logging
import os
import sys
import threading
import warnings
from contextlib import AbstractContextManager
from types import FrameType
from typing import Any, Dict, Optional, Set, Tuple, Union

try:
    from opentelemetry import trace as _otel_trace

    _HAS_OTEL = True
except ImportError:  # pragma: no cover
    _HAS_OTEL = False

from .config import LogCoreConfig, LogLevel, create_config
from .handlers import create_handlers
from .utils import (
    AsyncTimer,
    Timer,
    correlation_id_context,
    get_correlation_id,
    is_async_context,
    safe_str,
    set_correlation_id,
)

_srcfile = os.path.normcase(os.path.abspath(__file__))


def _find_caller() -> Tuple[str, int, str]:
    """Return (filename, lineno, funcname) of the first caller outside this module."""
    try:
        frame: Optional[FrameType] = sys._getframe(0)
    except AttributeError:
        return "(unknown file)", 0, "(unknown function)"
    while frame is not None:
        if os.path.normcase(os.path.abspath(frame.f_code.co_filename)) != _srcfile:
            return frame.f_code.co_filename, frame.f_lineno, frame.f_code.co_name
        frame = frame.f_back
    return "(unknown file)", 0, "(unknown function)"


_logger_lock = threading.RLock()
_loggers: Dict[str, "LogCoreLogger"] = {}


class LogCoreLogger:
    def __init__(self, config: LogCoreConfig):
        self.config = config

        self._logger = logging.getLogger(f"logcore.{config.name}")
        self._logger.setLevel(getattr(logging, config.level.value))

        self._logger.handlers.clear()

        handlers = create_handlers(config)
        for handler in handlers:
            handler.setLevel(getattr(logging, config.level.value))
            self._logger.addHandler(handler)

        if config.correlation_id:
            set_correlation_id(config.correlation_id)

    def _log(self, level: str, message: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.pop("exc_info", False)

        numeric_level = getattr(logging, level.upper(), logging.INFO)

        if not self._logger.isEnabledFor(numeric_level):
            return

        if exc_info is True:
            exc_info = sys.exc_info()

        fn, lno, func = _find_caller()
        record = self._logger.makeRecord(
            self._logger.name,
            numeric_level,
            fn,
            lno,
            message,
            args,
            exc_info=exc_info,
            func=func,
        )

        correlation_id = get_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id

        if _HAS_OTEL:
            _span = _otel_trace.get_current_span()
            if _span.is_recording():
                _ctx = _span.get_span_context()
                if _ctx.is_valid:
                    record.trace_id = format(_ctx.trace_id, "032x")
                    record.span_id = format(_ctx.span_id, "016x")

        for key, value in kwargs.items():
            if not hasattr(record, key):
                if isinstance(value, (bool, int, float, type(None))):
                    setattr(record, key, value)
                else:
                    setattr(record, key, safe_str(value))

        self._logger.handle(record)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("INFO", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("WARNING", message, *args, **kwargs)

    def warn(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("ERROR", message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("CRITICAL", message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = True
        self.error(message, *args, **kwargs)

    def time(
        self, operation_name: str, level: str = "INFO", **kwargs: Any
    ) -> Union[Timer, AsyncTimer]:
        """Return a context manager that logs start/complete and duration_ms.

        Auto-detects async context: returns AsyncTimer inside a running event
        loop task, Timer otherwise. Use with ``async with`` or ``with`` accordingly.
        """
        if is_async_context():
            return AsyncTimer(self, operation_name, level, **kwargs)
        else:
            return Timer(self, operation_name, level, **kwargs)

    def with_correlation_id(
        self, correlation_id: Optional[str] = None
    ) -> AbstractContextManager[str]:
        """Return a context manager that sets a correlation ID for this scope.

        Uses contextvars, so the ID is isolated per async task or thread.
        A UUID is generated automatically when correlation_id is omitted.
        """
        return correlation_id_context(correlation_id)

    def set_level(self, level: Union[str, LogLevel]) -> None:
        if isinstance(level, str):
            level = LogLevel.from_string(level)

        self.config.level = level
        numeric_level = getattr(logging, level.value)

        self._logger.setLevel(numeric_level)
        for handler in self._logger.handlers:
            handler.setLevel(numeric_level)

    def get_level(self) -> LogLevel:
        return self.config.level

    def is_enabled_for(self, level: Union[str, LogLevel]) -> bool:
        if isinstance(level, str):
            level = LogLevel.from_string(level)

        numeric_level = getattr(logging, level.value)
        return self._logger.isEnabledFor(numeric_level)


def get_logger(
    name: str,
    level: Optional[str] = None,
    json: Optional[bool] = None,
    file: Optional[str] = None,
    correlation_id: Optional[str] = None,
    max_file_size: Optional[int] = None,
    backup_count: Optional[int] = None,
    redact_fields: Optional[Set[str]] = None,
) -> "LogCoreLogger":
    """Return a LogCoreLogger for the given name, creating it if needed.

    Loggers are cached by name. Calling with the same name and no extra
    arguments returns the existing logger. Passing any configuration
    argument forces a new logger to be created and cached, replacing the old one.
    Environment variables (LOGCORE_*) are applied as defaults when a parameter
    is omitted.
    """
    with _logger_lock:
        if name in _loggers:
            existing_logger = _loggers[name]

            if all(
                param is None
                for param in [
                    level,
                    json,
                    file,
                    correlation_id,
                    max_file_size,
                    backup_count,
                    redact_fields,
                ]
            ):
                return existing_logger

            warnings.warn(
                f"Logger '{name}' already exists and is being replaced with new "
                "configuration. Existing references to the old logger will no longer "
                "receive log records.",
                UserWarning,
                stacklevel=2,
            )

        config = create_config(
            name=name,
            level=level,
            json=json,
            file=file,
            correlation_id=correlation_id,
            max_file_size=max_file_size,
            backup_count=backup_count,
            redact_fields=redact_fields,
        )

        logger = LogCoreLogger(config)
        _loggers[name] = logger

        return logger
