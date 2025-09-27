"""Core logging functionality for LogCore."""

import logging
import sys
import threading
from typing import Any, Dict, Optional, Set, Union

from .config import LogCoreConfig, LogLevel, create_config
from .handlers import create_handlers
from .utils import (
    Timer, AsyncTimer, correlation_id_context, get_correlation_id,
    set_correlation_id, safe_str, is_async_context
)


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
    
    def _log(self, level: str, message: str, *args, **kwargs):
        exc_info = kwargs.pop('exc_info', False)
        
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        if not self._logger.isEnabledFor(numeric_level):
            return
        
        record = self._logger.makeRecord(
            self._logger.name,
            numeric_level,
            "(unknown file)",
            0,
            message,
            args,
            exc_info=exc_info,
        )
        
        correlation_id = get_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id
        
        for key, value in kwargs.items():
            if not hasattr(record, key):
                setattr(record, key, safe_str(value))
        
        self._logger.handle(record)
    
    def debug(self, message: str, *args, **kwargs):
        self._log("DEBUG", message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self._log("INFO", message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log("WARNING", message, *args, **kwargs)
    
    def warn(self, message: str, *args, **kwargs):
        self.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log("ERROR", message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log("CRITICAL", message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        kwargs['exc_info'] = True
        self.error(message, *args, **kwargs)
    
    def time(self, operation_name: str, level: str = "INFO", **kwargs) -> Union[Timer, AsyncTimer]:
        if is_async_context():
            return AsyncTimer(self, operation_name, level, **kwargs)
        else:
            return Timer(self, operation_name, level, **kwargs)
    
    def with_correlation_id(self, correlation_id: Optional[str] = None):
        return correlation_id_context(correlation_id)
    
    def set_level(self, level: Union[str, LogLevel]):
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
) -> LogCoreLogger:
    with _logger_lock:
        if name in _loggers:
            existing_logger = _loggers[name]
            
            if all(param is None for param in [
                level, json, file, correlation_id, max_file_size,
                backup_count, redact_fields
            ]):
                return existing_logger
        
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
