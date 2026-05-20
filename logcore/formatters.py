"""Formatters for LogCore logging output."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Set, Optional

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


# All standard LogRecord attributes plus logcore fields that are emitted
# explicitly (e.g. correlation_id). Shared between both formatters so that
# adding a field in one place covers both.
_STDLIB_LOG_FIELDS: frozenset = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "lineno", "funcName", "created",
    "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message",
    "exc_info", "exc_text", "stack_info", "taskName",
    "correlation_id",
})


class RedactingFormatter:
    """Base formatter with partial masking of sensitive fields."""

    def __init__(self, redact_fields: Optional[Set[str]] = None):
        self.redact_fields = redact_fields or set()
        self.redact_pattern = self._build_pattern()

    @staticmethod
    def _mask(value: Any) -> str:
        """Return a partially masked string, revealing only a short prefix.

        Values of 4 chars or fewer are fully redacted because any prefix
        would reveal a significant fraction of the secret.
        """
        s = str(value)
        if len(s) <= 4:
            return "[REDACTED]"
        prefix_len = min(4, max(1, len(s) // 4))
        return s[:prefix_len] + "***"

    def _build_pattern(self) -> Optional[re.Pattern]:
        if not self.redact_fields:
            return None
        fields = "|".join(re.escape(f) for f in self.redact_fields)
        pattern = rf'("{fields}"|{fields})(\s*[:=]\s*)("[^"]*"|[^\s,\]}}]+)'
        return re.compile(pattern, re.IGNORECASE)

    def _redact_text(self, text: str) -> str:
        if not self.redact_pattern:
            return text

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            sep = match.group(2)
            raw = match.group(3)
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1]
            return f'{key}{sep}"{self._mask(raw)}"'

        return self.redact_pattern.sub(replace, text)

    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.redact_fields:
            return data

        result: Dict[str, Any] = {}
        redact_keys = {f.lower() for f in self.redact_fields}

        for key, value in data.items():
            if key.lower() in redact_keys:
                result[key] = self._mask(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            else:
                result[key] = value

        return result


class JSONFormatter(RedactingFormatter, logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, redact_fields: Optional[Set[str]] = None):
        super().__init__(redact_fields=redact_fields)
        logging.Formatter.__init__(self)

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "correlation_id") and record.correlation_id:
            entry["correlation_id"] = record.correlation_id
        
        for key, value in record.__dict__.items():
            if key not in _STDLIB_LOG_FIELDS:
                entry[key] = value

        if record.exc_info:
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
    
    def __init__(self, redact_fields: Optional[Set[str]] = None, use_colors: Optional[bool] = None):
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
        
        extras = []

        for key, value in record.__dict__.items():
            if key not in _STDLIB_LOG_FIELDS:
                extras.append(f"{key}={value}")
        
        extra_part = " " + " ".join(extras) if extras else ""
        
        formatted = f"{timestamp} {level} {record.name}{correlation_part}: {message}{extra_part}"
        
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return self._redact_text(formatted)
