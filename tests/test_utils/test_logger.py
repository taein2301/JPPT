import os
from pathlib import Path

from loguru import logger

from src.utils.logger import (
    _log_namer,
    _make_retention_handler,
    _parse_retention_days,
    setup_logger,
)


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


def test_log_namer_converts_date_format() -> None:
    """로테이션된 로그 파일명이 _YYYYMMDD.log 형식으로 변환되는지 검증."""
    result = _log_namer("/logs/app.log.2026-02-06_00-00-00_000000")
    assert result == str(Path("/logs") / "app_20260206.log")


def test_log_namer_with_batch_log() -> None:
    """배치 모드 로그 파일명도 올바르게 변환되는지 검증."""
    result = _log_namer("/logs/app_batch.log.2026-01-15_23-59-59_999999")
    assert result == str(Path("/logs") / "app_batch_20260115.log")


def test_log_namer_no_match_returns_original() -> None:
    """날짜 패턴이 없으면 원본 경로를 그대로 반환하는지 검증."""
    result = _log_namer("/logs/app.log")
    assert result == "/logs/app.log"


def test_parse_retention_days() -> None:
    """retention 문자열 파싱 검증."""
    assert _parse_retention_days("10 days") == 10
    assert _parse_retention_days("1 day") == 1
    assert _parse_retention_days("2 weeks") == 14
    assert _parse_retention_days("1 week") == 7
    assert _parse_retention_days("invalid") == 10  # default


def test_retention_handler_renames_rotated_file(tmp_path: Path) -> None:
    """retention 핸들러가 로테이션된 파일을 _YYYYMMDD.log로 이름변경하는지 검증."""
    log_file = tmp_path / "app.log"
    handler = _make_retention_handler("10 days", log_file)

    # Loguru 기본 형식의 백업 파일 생성
    rotated = tmp_path / "app.log.2026-02-05_00-00-00_000000"
    rotated.write_text("old log")

    handler([str(rotated)])

    # _YYYYMMDD.log 형식으로 이름변경 확인
    renamed = tmp_path / "app_20260205.log"
    assert renamed.exists()
    assert renamed.read_text() == "old log"
    assert not rotated.exists()


def test_retention_handler_deletes_old_files(tmp_path: Path) -> None:
    """retention 핸들러가 보관기간 초과 파일을 삭제하는지 검증."""
    log_file = tmp_path / "app.log"
    handler = _make_retention_handler("1 day", log_file)

    # 오래된 백업 파일 생성 (30일 전)
    old_file = tmp_path / "app_20260101.log"
    old_file.write_text("very old")
    # mtime을 과거로 설정
    os.utime(old_file, (0, 0))

    handler([])

    assert not old_file.exists()


def test_retention_handler_keeps_recent_files(tmp_path: Path) -> None:
    """retention 핸들러가 보관기간 내 파일은 유지하는지 검증."""
    log_file = tmp_path / "app.log"
    handler = _make_retention_handler("10 days", log_file)

    # 오늘 날짜의 백업 파일 생성
    from datetime import datetime

    today = datetime.now().strftime("%Y%m%d")
    recent_file = tmp_path / f"app_{today}.log"
    recent_file.write_text("recent log")

    handler([])

    assert recent_file.exists()
