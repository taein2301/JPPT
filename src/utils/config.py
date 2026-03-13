"""Pydantic Settings를 사용한 설정 관리.

이 모듈은 YAML 파일 기반의 계층적 설정 시스템을 제공합니다.
기본 설정(default.yaml)과 환경별 설정(dev.yaml, prod.yaml)을 병합하여 사용합니다.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    json_logs: bool = Field(default=False)


class TelegramConfig(BaseModel):
    """텔레그램 연동 설정.

    Attributes:
        enabled: 텔레그램 알림 활성화 여부
        bot_token: 텔레그램 봇 토큰
        chat_id: 텔레그램 채팅방 ID
    """

    enabled: bool = Field(default=False)
    bot_token: str = Field(default="")
    chat_id: str = Field(default="")


class ApiConfig(BaseModel):
    """FastAPI 서버 설정.

    Attributes:
        host: 서버 바인딩 호스트
        port: 서버 포트
        reload: 개발용 자동 리로드 여부
        docs_enabled: Swagger/OpenAPI 문서 노출 여부
        cors_origins: 허용할 CORS Origin 목록
        trusted_hosts: 허용할 Host 헤더 목록
        root_path: 프록시 환경에서 사용할 루트 경로
    """

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    docs_enabled: bool = Field(default=True)
    cors_origins: list[str] = Field(default_factory=list)
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    root_path: str = Field(default="")


class Settings(BaseSettings):
    """YAML 파일에서 로드된 애플리케이션 전체 설정.

    Attributes:
        app: 애플리케이션 기본 설정
        logging: 로깅 설정
        telegram: 텔레그램 연동 설정
        api: FastAPI 서버 설정
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="forbid",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """중첩 딕셔너리를 재귀적으로 병합합니다."""
    merged = deepcopy(base)

    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
            continue

        merged[key] = deepcopy(value)

    return merged


def load_config(env: str = "dev", config_dir: Path | None = None) -> Settings:
    """YAML 파일에서 설정을 로드합니다.

    환경별 설정 파일({env}.yaml)을 로드합니다.

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

    default_config_file = config_dir / "default.yaml"
    config_file = config_dir / f"{env}.yaml"

    if not default_config_file.exists():
        raise ConfigurationError(f"Default config file not found: {default_config_file}")

    if not config_file.exists():
        raise ConfigurationError(
            f"Config file not found: {config_file}\n"
            f"Please create {env}.yaml from {env}.yaml.example template"
        )

    with default_config_file.open(encoding="utf-8") as f:
        default_config_data: dict[str, Any] = yaml.safe_load(f) or {}

    with config_file.open(encoding="utf-8") as f:
        env_config_data: dict[str, Any] = yaml.safe_load(f) or {}

    config_data = _deep_merge(default_config_data, env_config_data)

    return Settings(**config_data)
