"""
OpenSearch by DeepLogic — Logging Subsystem
Configures local file logging with rotation and console stream logging.
"""

from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from utils.paths import get_logs_dir

_LOGGER_INITIALIZED = False


def setup_logger(name: str = "OpenSearch", level: int = logging.INFO) -> logging.Logger:
    """Initialize and configure application logger."""
    global _LOGGER_INITIALIZED
    logger = logging.getLogger(name)

    if not _LOGGER_INITIALIZED:
        logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler (Rotating: 5 MB each, up to 5 backups)
        log_file = get_logs_dir() / "opensearch.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(console_handler)

        _LOGGER_INITIALIZED = True

    return logger


logger = setup_logger()
