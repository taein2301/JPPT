"""Loguru를 사용한 로깅 설정.

이 모듈은 콘솔 및 파일 로깅을 설정하고, 로그 로테이션 및 보관 정책을 관리합니다.
로테이션 시 백업 파일은 _YYYYMMDD.log 형식으로 저장됩니다.
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from loguru import logger


def _log_namer(filepath: str) -> str:
    """로테이션된 로그 파일명을 _YYYYMMDD.log 형식으로 변환합니다.

    Loguru 기본 백업 형식: app.log.2026-02-06_00-00-00_000000
    변환 결과: app_20260206.log
    """
    match = re.search(r"\.(\d{4})-(\d{2})-(\d{2})_\d{2}-\d{2}-\d{2}_\d+$", filepath)
    if not match:
        return filepath
    year, month, day = match.group(1), match.group(2), match.group(3)
    base = filepath[: match.start()]
    stem = Path(base).stem
    ext = Path(base).suffix
    parent = str(Path(base).parent)
    return str(Path(parent) / f"{stem}_{year}{month}{day}{ext}")


def _parse_retention_days(retention: str) -> int:
    """retention 문자열을 일(day) 단위로 파싱합니다."""
    match = re.match(r"(\d+)\s*(day|days|week|weeks)", retention.strip())
    if not match:
        return 10
    value = int(match.group(1))
    unit = match.group(2)
    if "week" in unit:
        return value * 7
    return value


def _make_retention_handler(retention: str, log_file: Path) -> Callable[[list[str]], None]:
    """_YYYYMMDD.log 이름변경 + 보관기간 관리를 수행하는 retention 핸들러를 생성합니다.

    Loguru의 retention 콜백으로 사용됩니다. 로테이션 시:
    1. Loguru 기본 형식(app.log.YYYY-MM-DD_...)을 app_YYYYMMDD.log로 이름변경
    2. 이전에 이름변경된 파일 포함, 보관기간 초과 파일 삭제
    """
    max_age_days = _parse_retention_days(retention)
    stem = log_file.stem
    ext = log_file.suffix
    log_dir = log_file.parent

    def handler(logs: list[str]) -> None:
        now = datetime.now()
        cutoff = now - timedelta(days=max_age_days)

        # 1. Loguru 기본 형식 파일을 _YYYYMMDD.log로 이름변경
        for log_path in logs:
            match = re.search(r"\.(\d{4})-(\d{2})-(\d{2})_\d{2}-\d{2}-\d{2}_\d+$", log_path)
            if match:
                new_path = _log_namer(log_path)
                if os.path.exists(new_path):
                    os.remove(log_path)
                else:
                    os.rename(log_path, new_path)

        # 2. 이름변경된 파일(_YYYYMMDD.log) 중 보관기간 초과 파일 삭제
        pattern = re.compile(rf"^{re.escape(stem)}_(\d{{8}}){re.escape(ext)}$")
        if log_dir.exists():
            for f in log_dir.iterdir():
                m = pattern.match(f.name)
                if m:
                    try:
                        file_date = datetime.strptime(m.group(1), "%Y%m%d")
                        if file_date < cutoff:
                            f.unlink(missing_ok=True)
                    except ValueError:
                        continue

    return handler


def setup_logger(
    level: str = "INFO",
    log_file: Path | None = None,
    format_str: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    ),
    rotation: str = "00:00",
    retention: str = "10 days",
) -> None:
    """Loguru 로거를 설정합니다.

    기본 핸들러를 제거하고 콘솔 및 파일 핸들러를 추가합니다.
    콘솔 출력은 색상이 적용되며, 파일 로깅은 자동 로테이션을 지원합니다.
    로테이션 시 백업 파일은 {stem}_YYYYMMDD{ext} 형식으로 저장됩니다.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (옵션, None이면 파일 로깅 비활성화)
        format_str: 로그 포맷 문자열
        rotation: 로그 파일 로테이션 주기 (시간 또는 크기, 예: "00:00", "100 MB")
        retention: 로그 파일 보관 기간 (예: "10 days", "1 week")
    """
    # 기본 핸들러 제거 (깨끗한 상태로 시작)
    logger.remove()

    # 콘솔 핸들러 추가 (색상, backtrace, diagnose 활성화)
    logger.add(
        sys.stderr,
        format=format_str,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        # 로그 디렉토리가 없으면 생성
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=format_str,
            level=level,
            rotation=rotation,
            retention=_make_retention_handler(retention, log_file),
            compression=None,
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logger initialized: level={level}, file={log_file}")
