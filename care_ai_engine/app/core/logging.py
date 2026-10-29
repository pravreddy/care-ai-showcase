"""
Care AI Engine - Structured Logging
Production-grade JSON logging with correlation IDs.
"""

import logging
import logging.handlers
import sys
import json
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar
from pathlib import Path

from app.core.config import get_settings

# Correlation ID for request tracing
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="system")


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get("system"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Include any extra fields
        for key in ("user_id", "endpoint", "status_code", "duration_ms", "query"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        cid = correlation_id.get("system")[:8]
        return (
            f"{color}{record.levelname:<8}{self.RESET} "
            f"[{cid}] "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear existing handlers
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json" and settings.is_production:
        console.setFormatter(JSONFormatter())
    else:
        console.setFormatter(HumanFormatter())
    root.addHandler(console)

    # File handler (production only)
    if settings.is_production:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
        )
        file_handler.setFormatter(JSONFormatter())
        root.addHandler(file_handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(f"careai.{name}")


def new_correlation_id() -> str:
    """Generate a new correlation ID for request tracing."""
    cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid
