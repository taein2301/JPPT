"""Loguru를 사용한 로깅 설정.

이 모듈은 콘솔 및 파일 로깅을 설정하고, 로그 로테이션 및 보관 정책을 관리합니다.
"""

import sys
from pathlib import Path

from loguru import logger


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
            retention=retention,
            compression=None,
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logger initialized: level={level}, file={log_file}")
