"""Core logging functionality for LogCore."""

import logging
import os
import sys
import threading
import warnings
from contextlib import contextmanager
from types import FrameType
from typing import Any, Dict, Generator, Optional, Set, Tuple, Union

try:
    from opentelemetry import trace as _otel_trace

    _HAS_OTEL = True
except ImportError:  # pragma: no cover
    _HAS_OTEL = False

from .config import LogCoreConfig, LogLevel, create_config
from .handlers import create_handlers
from .sampling import Decision, Sampler
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
        self.sampler: Optional[Sampler] = config.sampler

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

        if self.sampler is not None:
            decision = self.sampler.decide(record)
            if decision is Decision.DROP:
                self.sampler._record_dropped()
                return
            if decision is Decision.BUFFER:
                self.sampler.buffer(record)
                return
            for buffered in self.sampler.flush_pending(record):
                self._logger.handle(buffered)
            self.sampler._record_kept()

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

    @contextmanager
    def with_correlation_id(
        self, correlation_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Return a context manager that sets a correlation ID for this scope.

        Uses contextvars, so the ID is isolated per async task or thread.
        A UUID is generated automatically when correlation_id is omitted.

        When a tail-based sampler is attached, any buffered records for this
        correlation_id are discarded on clean exit (the request didn't error,
        so we drop the captured history).
        """
        with correlation_id_context(correlation_id) as cid:
            try:
                yield cid
            finally:
                if self.sampler is not None and self.sampler.tail_based:
                    self.sampler.discard_buffer(cid)

    def flush_sample_buffer(self, correlation_id: Optional[str] = None) -> int:
        """Discard any tail-buffered records for ``correlation_id``.

        Call this at request end when you set the correlation_id directly
        (e.g. via middleware) instead of using ``with_correlation_id``. When
        ``correlation_id`` is omitted, the current contextvar value is used.

        Returns the number of records discarded; 0 if no sampler is attached,
        sampling is not tail-based, or no buffer exists for the given cid.
        """
        if self.sampler is None or not self.sampler.tail_based:
            return 0
        cid = correlation_id if correlation_id is not None else get_correlation_id()
        if cid is None:
            return 0
        return self.sampler.discard_buffer(cid)

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
    sampler: Optional[Sampler] = None,
    sample_rate: Optional[float] = None,
) -> "LogCoreLogger":
    """Return a LogCoreLogger for the given name, creating it if needed.

    Loggers are cached by name. Calling with the same name and no extra
    arguments returns the existing logger. Passing any configuration
    argument forces a new logger to be created and cached, replacing the old one.
    Environment variables (LOGCORE_*) are applied as defaults when a parameter
    is omitted.

    Pass ``sampler`` for full control, or ``sample_rate`` as a shortcut for
    ``Sampler(rate=sample_rate)``. Passing both raises ``ValueError``.
    """
    if sampler is not None and sample_rate is not None:
        raise ValueError("Pass either `sampler` or `sample_rate`, not both.")

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
                    sampler,
                    sample_rate,
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
            sampler=sampler,
            sample_rate=sample_rate,
        )

        logger = LogCoreLogger(config)
        _loggers[name] = logger

        return logger
