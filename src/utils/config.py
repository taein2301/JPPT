"""Pydantic Settings를 사용한 설정 관리.

이 모듈은 YAML 파일 기반의 환경별 설정 시스템을 제공합니다.
환경별 설정(dev.yaml, prod.yaml)을 직접 로드하여 사용합니다.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
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
    silent_time: "TelegramSilentTimeConfig" = Field(
        default_factory=lambda: TelegramSilentTimeConfig()
    )
    templates: "TelegramMessageTemplateConfig" = Field(
        default_factory=lambda: TelegramMessageTemplateConfig()
    )


class TelegramMessageTemplateConfig(BaseModel):
    """텔레그램 메시지 템플릿 설정.

    Attributes:
        error_alert: 오류 알림 템플릿
    """

    error_alert: str = Field(
        default=(
            "🚨 **Error Alert**\n\n"
            "{context_section}"
            "**Error:** `{error_type}`\n"
            "**Message:** {error_message}"
        )
    )


class TelegramSilentTimeConfig(BaseModel):
    """텔레그램 무음 시간 설정.

    Attributes:
        enabled: 무음 시간 적용 여부
        start: 시작 시각 (HH:MM)
        end: 종료 시각 (HH:MM)
        timezone: 시각 판정에 사용할 IANA 타임존
    """

    enabled: bool = Field(default=False)
    start: str = Field(default="23:00")
    end: str = Field(default="08:00")
    timezone: str = Field(default="Asia/Seoul")

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        """HH:MM 형식의 시각 문자열인지 검증합니다."""
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("Time must be in HH:MM format") from exc
        return value

    @model_validator(mode="after")
    def validate_timezone_when_enabled(self) -> "TelegramSilentTimeConfig":
        """silent time 활성화 시에만 IANA 타임존을 검증합니다."""
        if not self.enabled:
            return self

        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Timezone must be a valid IANA timezone") from exc
        return self


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

    config_file = config_dir / f"{env}.yaml"

    if not config_file.exists():
        raise ConfigurationError(
            f"Config file not found: {config_file}\n"
            f"Please create {env}.yaml from {env}.yaml.example template"
        )

    with config_file.open(encoding="utf-8") as f:
        config_data: dict[str, Any] = yaml.safe_load(f) or {}

    return Settings(**config_data)
