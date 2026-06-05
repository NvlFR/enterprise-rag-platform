import json
import logging
import sys
from contextvars import ContextVar

from app.core.config import settings

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "request_id": request_id_var.get(),
        }

        # Include extra fields if provided
        if hasattr(record, "extra_info"):
            log_record.update(record.extra_info)

        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging() -> None:
    """
    Setup logging configuration based on settings.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT.upper() == "JSON":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s - %(levelname)s - [%(request_id)s] - "
                "%(name)s - %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set external loggers to a higher level to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request_id to the record for text formatting.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


# Apply filter to all root handlers if using text format
def apply_request_id_filter() -> None:
    if settings.LOG_FORMAT.upper() != "JSON":
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.addFilter(RequestIDFilter())


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)
