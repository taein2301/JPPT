from pathlib import Path

from loguru import logger
from src.utils.logger import setup_logger


def test_setup_logger_console_only(tmp_path: Path) -> None:
    logger.remove()  # Clear existing handlers

    setup_logger(level="DEBUG", log_file=None, format_str="{level} | {message}")

    # Logger should be configured
    assert len(logger._core.handlers) > 0


def test_setup_logger_with_file(tmp_path: Path) -> None:
    logger.remove()

    log_file = tmp_path / "test.log"
    setup_logger(
        level="INFO",
        log_file=log_file,
        format_str="{level} | {message}",
        rotation="1 MB",
        retention="1 day",
    )

    # Log a message
    logger.info("test message")

    # File should be created
    assert log_file.exists()
    assert "test message" in log_file.read_text()
