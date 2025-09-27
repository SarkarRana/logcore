"""Custom handlers for LogForge."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .formatters import JSONFormatter, TextFormatter
from .config import LogForgeConfig


class ConsoleHandler:
    def __init__(self, config: LogForgeConfig):
        self.config = config
        self.handler = logging.StreamHandler(sys.stderr)
        formatter = JSONFormatter(redact_fields=config.redact_fields) if config.json else TextFormatter(redact_fields=config.redact_fields)
        self.handler.setFormatter(formatter)
    
    def get_handler(self) -> logging.Handler:
        return self.handler


class FileHandler:
    def __init__(self, config: LogForgeConfig, file_path: str):
        self.config = config
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.handler = logging.handlers.RotatingFileHandler(
            filename=str(file_path),
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding="utf-8"
        )
        
        formatter = JSONFormatter(redact_fields=config.redact_fields) if config.json else TextFormatter(redact_fields=config.redact_fields)
        self.handler.setFormatter(formatter)
    
    def get_handler(self) -> logging.Handler:
        return self.handler


def create_handlers(config: LogForgeConfig) -> list[logging.Handler]:
    handlers = []
    
    console_handler = ConsoleHandler(config)
    handlers.append(console_handler.get_handler())
    
    if config.file:
        file_handler = FileHandler(config, config.file)
        handlers.append(file_handler.get_handler())
    
    return handlers
