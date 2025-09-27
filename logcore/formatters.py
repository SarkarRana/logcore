"""Formatters for LogCore logging output."""

import json
import logging
import re
import sys
from datetime import datetime
from typing import Any, Dict, Set

try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    HAS_COLORS = True
except ImportError:
    HAS_COLORS = False
    
    class Fore:
        RED = YELLOW = GREEN = BLUE = CYAN = MAGENTA = WHITE = ""
    
    class Style:
        RESET_ALL = BRIGHT = ""


class RedactingFormatter:
    """Base formatter with redaction."""
    
    def __init__(self, redact_fields: Set[str] = None):
        self.redact_fields = redact_fields or set()
        self.redact_pattern = self._build_pattern()
    
    def _build_pattern(self):
        if not self.redact_fields:
            return None
        
        fields = "|".join(re.escape(field) for field in self.redact_fields)
        pattern = rf'("{fields}"|{fields})(\s*[:=]\s*)("[^"]*"|[^\s,\]}}]+)'
        return re.compile(pattern, re.IGNORECASE)
    
    def _redact_text(self, text: str) -> str:
        if not self.redact_pattern:
            return text
        
        def replace(match):
            key = match.group(1)
            sep = match.group(2)
            return f'{key}{sep}"[REDACTED]"'
        
        return self.redact_pattern.sub(replace, text)
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.redact_fields:
            return data
        
        result = {}
        redact_keys = {field.lower() for field in self.redact_fields}
        
        for key, value in data.items():
            if key.lower() in redact_keys:
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            else:
                result[key] = value
        
        return result


class JSONFormatter(RedactingFormatter, logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, redact_fields: Set[str] = None):
        super().__init__(redact_fields=redact_fields)
        logging.Formatter.__init__(self)
    
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "correlation_id") and record.correlation_id:
            entry["correlation_id"] = record.correlation_id
        
        skip_fields = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "lineno", "funcName", "created",
            "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "correlation_id"
        }
        
        for key, value in record.__dict__.items():
            if key not in skip_fields:
                entry[key] = value
        
        if record.exc_info and record.exc_info != True:
            entry["exception"] = self.formatException(record.exc_info)
        
        entry = self._redact_dict(entry)
        return json.dumps(entry, default=str, ensure_ascii=False)


class TextFormatter(RedactingFormatter, logging.Formatter):
    """Text formatter with colors."""
    
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }
    
    def __init__(self, redact_fields: Set[str] = None, use_colors: bool = None):
        super().__init__(redact_fields=redact_fields)
        
        if use_colors is None:
            use_colors = HAS_COLORS and hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
        
        self.use_colors = use_colors
        logging.Formatter.__init__(self)
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level = f"{color}{level:8}{Style.RESET_ALL}"
        else:
            level = f"{level:8}"
        
        message = record.getMessage()
        
        correlation_part = ""
        if hasattr(record, "correlation_id") and record.correlation_id:
            correlation_part = f" [cid={record.correlation_id}]"
        
        skip_fields = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "lineno", "funcName", "created",
            "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "correlation_id"
        }
        
        extras = []
        redact_keys = {field.lower() for field in self.redact_fields}
        
        for key, value in record.__dict__.items():
            if key not in skip_fields:
                if key.lower() in redact_keys:
                    value = "[REDACTED]"
                extras.append(f"{key}={value}")
        
        extra_part = " " + " ".join(extras) if extras else ""
        
        formatted = f"{timestamp} {level} {record.name}{correlation_part}: {message}{extra_part}"
        
        if record.exc_info and record.exc_info != True:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return self._redact_text(formatted)
