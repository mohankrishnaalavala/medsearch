"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
    
    # JSON formatter for file logging
    json_formatter = jsonlogger.JsonFormatter(
        fmt=log_format,
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    
    # Standard formatter for console
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with JSON formatting
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)

    # Console handler with standard formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

