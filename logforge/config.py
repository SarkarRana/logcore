"""Configuration management for LogCore."""

import os
from enum import Enum
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        level = level.upper()
        if level == "WARN":
            return cls.WARNING
        return cls(level)


@dataclass
class LogCoreConfig:
    name: str
    level: LogLevel = LogLevel.INFO
    json: bool = False
    file: Optional[str] = None
    correlation_id: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024
    backup_count: int = 5
    redact_fields: Set[str] = None
    
    def __post_init__(self):
        if self.redact_fields is None:
            self.redact_fields = {
                "password", "passwd", "secret", "token", "key", "api_key",
                "access_token", "auth", "authorization", "credential",
                "private_key", "cert", "certificate"
            }


def get_config_from_env() -> Dict[str, Any]:
    config = {}
    
    if level := os.getenv("LOGCORE_LEVEL"):
        try:
            config["level"] = LogLevel.from_string(level)
        except ValueError:
            pass
    
    if json_env := os.getenv("LOGCORE_JSON"):
        config["json"] = json_env.lower() in ("true", "1", "yes", "on")
    
    if file_path := os.getenv("LOGCORE_FILE"):
        config["file"] = file_path
    
    if correlation_id := os.getenv("LOGCORE_CORRELATION_ID"):
        config["correlation_id"] = correlation_id
    
    if max_size := os.getenv("LOGCORE_MAX_FILE_SIZE"):
        try:
            config["max_file_size"] = int(max_size)
        except ValueError:
            pass
    
    if backup_count := os.getenv("LOGCORE_BACKUP_COUNT"):
        try:
            config["backup_count"] = int(backup_count)
        except ValueError:
            pass
    
    if redact_fields := os.getenv("LOGCORE_REDACT_FIELDS"):
        config["redact_fields"] = set(field.strip() for field in redact_fields.split(","))
    
    return config


def create_config(
    name: str,
    level: Optional[str] = None,
    json: Optional[bool] = None,
    file: Optional[str] = None,
    correlation_id: Optional[str] = None,
    max_file_size: Optional[int] = None,
    backup_count: Optional[int] = None,
    redact_fields: Optional[Set[str]] = None,
) -> LogCoreConfig:
    env_config = get_config_from_env()
    
    config_dict = {
        "name": name,
        "level": LogLevel.from_string(level) if level else env_config.get("level", LogLevel.INFO),
        "json": json if json is not None else env_config.get("json", False),
        "file": file if file is not None else env_config.get("file"),
        "correlation_id": correlation_id if correlation_id is not None else env_config.get("correlation_id"),
        "max_file_size": max_file_size if max_file_size is not None else env_config.get("max_file_size", 10 * 1024 * 1024),
        "backup_count": backup_count if backup_count is not None else env_config.get("backup_count", 5),
        "redact_fields": redact_fields if redact_fields is not None else env_config.get("redact_fields"),
    }
    
    return LogCoreConfig(**config_dict)
