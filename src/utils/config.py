"""Pydantic Settings를 사용한 설정 관리.

이 모듈은 YAML 파일 기반의 계층적 설정 시스템을 제공합니다.
기본 설정(default.yaml)과 환경별 설정(dev.yaml, prod.yaml)을 병합하여 사용합니다.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """애플리케이션 기본 설정.

    Attributes:
        name: 애플리케이션 이름
        version: 애플리케이션 버전
        debug: 디버그 모드 활성화 여부
    """

    name: str = Field(default="jppt")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """로깅 설정.

    Attributes:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: 로그 포맷 문자열
        rotation: 로그 파일 로테이션 주기 (시간 또는 크기)
        retention: 로그 파일 보관 기간
    """

    level: str = Field(default="INFO")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )
    rotation: str = Field(default="00:00")
    retention: str = Field(default="10 days")


class TelegramConfig(BaseModel):
    """텔레그램 연동 설정.

    Attributes:
        enabled: 텔레그램 알림 활성화 여부
        bot_token: 텔레그램 봇 토큰 (환경변수에서 로드 권장)
        chat_id: 텔레그램 채팅방 ID
    """

    enabled: bool = Field(default=False)
    bot_token: str = Field(default="")
    chat_id: str = Field(default="")


class Settings(BaseSettings):
    """YAML 파일에서 로드된 애플리케이션 전체 설정.

    Attributes:
        app: 애플리케이션 기본 설정
        logging: 로깅 설정
        telegram: 텔레그램 연동 설정
    """

    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


def load_config(env: str = "dev", config_dir: Path | None = None) -> Settings:
    """YAML 파일에서 설정을 로드합니다.

    default.yaml과 {env}.yaml을 병합하여 최종 설정을 생성합니다.
    환경별 설정이 기본 설정을 오버라이드합니다.

    Args:
        env: 환경 이름 (dev, prod 등)
        config_dir: 설정 파일 디렉토리 경로 (기본값: 프로젝트 루트의 config/)

    Returns:
        로드된 설정이 담긴 Settings 객체

    Raises:
        ConfigurationError: 설정 파일이 없거나 유효하지 않은 경우
    """
    from src.utils.exceptions import ConfigurationError

    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"

    default_file = config_dir / "default.yaml"
    env_file = config_dir / f"{env}.yaml"

    if not default_file.exists():
        raise ConfigurationError(f"Default config not found: {default_file}")

    # Load default config
    with open(default_file) as f:
        default_data: dict[str, Any] = yaml.safe_load(f) or {}

    # Merge with environment-specific config if exists
    if env_file.exists():
        with open(env_file) as f:
            env_data: dict[str, Any] = yaml.safe_load(f) or {}
            # Deep merge
            for key, value in env_data.items():
                if key in default_data and isinstance(default_data[key], dict):
                    default_data[key].update(value)
                else:
                    default_data[key] = value

    # Override with environment variables
    if bot_token := os.getenv("TELEGRAM_BOT_TOKEN"):
        default_data.setdefault("telegram", {})["bot_token"] = bot_token
    if chat_id := os.getenv("TELEGRAM_CHAT_ID"):
        default_data.setdefault("telegram", {})["chat_id"] = chat_id

    return Settings(**default_data)
