"""LogCore - Production logging for Python."""

from .config import LogLevel
from .logger import get_logger
from .sampling import Sampler
from .utils import get_correlation_id, set_correlation_id

__version__ = "0.1.5"
__all__ = [
    "get_logger",
    "LogLevel",
    "set_correlation_id",
    "get_correlation_id",
    "Sampler",
]
