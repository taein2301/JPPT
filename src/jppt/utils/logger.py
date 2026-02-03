"""Logging configuration using Loguru."""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: Path | None = None,
    format_str: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | " "{name}:{function}:{line} | {message}"
    ),
    rotation: str = "00:00",
    retention: str = "10 days",
) -> None:
    """
    Configure Loguru logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_str: Log format string
        rotation: When to rotate log file (time or size)
        retention: How long to keep old logs
    """
    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stderr,
        format=format_str,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=format_str,
            level=level,
            rotation=rotation,
            retention=retention,
            compression=None,
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logger initialized: level={level}, file={log_file}")
