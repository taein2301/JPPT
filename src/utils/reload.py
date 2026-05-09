"""런타임 설정 reload 조정기.

이 모듈은 설정 파일을 다시 로드하고, 적용 콜백이 성공한 경우에만
현재 설정을 교체하는 순수 coordinator를 제공합니다.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from src.utils.config import Settings, load_config

ApplySettings = Callable[[Settings], Awaitable[None]]


@dataclass(frozen=True)
class ReloadResult:
    """설정 reload 실행 결과.

    Attributes:
        succeeded: reload 성공 여부
        message: 사람이 읽을 수 있는 결과 메시지
        settings: 성공 시 새 설정, 실패 시 기존 설정
        error_type: 실패한 예외 타입 이름
        error_message: 실패한 예외 메시지
    """

    succeeded: bool
    message: str
    settings: Settings
    error_type: str | None = None
    error_message: str | None = None


class ReloadCoordinator:
    """설정 reload 상태와 적용 순서를 관리합니다."""

    def __init__(
        self,
        *,
        settings: Settings,
        env: str,
        config_dir: Path | None,
        apply_settings: ApplySettings,
    ) -> None:
        """ReloadCoordinator를 초기화합니다.

        Args:
            settings: 현재 실행 중인 설정
            env: 다시 로드할 설정 환경 이름
            config_dir: 설정 파일 디렉토리
            apply_settings: 새 설정을 런타임 리소스에 적용하는 async 콜백
        """
        self.current_settings = settings
        self.env = env
        self.config_dir = config_dir
        self.apply_settings = apply_settings
        self.reload_count = 0
        self.last_reload_status = "never"
        self.last_reload_at: datetime | None = None
        self.last_reload_error: str | None = None
        self._started_at = monotonic()
        self._lock = asyncio.Lock()

    async def reload(self) -> ReloadResult:
        """설정을 다시 로드하고 적용에 성공한 경우에만 현재 설정을 교체합니다."""
        async with self._lock:
            try:
                next_settings = load_config(env=self.env, config_dir=self.config_dir)
                await self.apply_settings(next_settings)
            except Exception as exc:  # noqa: BLE001 - 실패 상태를 결과로 반환해야 한다.
                error_type = type(exc).__name__
                error_message = "config reload failed"
                self.last_reload_status = "failed"
                self.last_reload_at = datetime.now(tz=UTC)
                self.last_reload_error = f"{error_type}: {error_message}"
                return ReloadResult(
                    succeeded=False,
                    message=f"Config reload failed: {self.last_reload_error}",
                    settings=self.current_settings,
                    error_type=error_type,
                    error_message=error_message,
                )

            self.current_settings = next_settings
            self.reload_count += 1
            self.last_reload_status = "success"
            self.last_reload_at = datetime.now(tz=UTC)
            self.last_reload_error = None
            return ReloadResult(
                succeeded=True,
                message=f"Config reload succeeded: env={self.env} app={next_settings.app.name}",
                settings=next_settings,
            )

    def status_message(self) -> str:
        """현재 reload 상태를 Telegram 전송용 plain text로 반환합니다."""
        app_name = self.current_settings.app.name.strip().upper() or "APP"
        remote_control_status = (
            "enabled" if self.current_settings.telegram.remote_control.enabled else "disabled"
        )
        uptime_seconds = int(monotonic() - self._started_at)
        lines = [
            f"[{app_name}] config reload status",
            f"Env : {self.env}",
            f"Uptime Seconds : {uptime_seconds}",
            f"Remote Control : {remote_control_status}",
            f"Reload Count : {self.reload_count}",
            f"Last Reload Status : {self.last_reload_status}",
        ]

        if self.last_reload_at is not None:
            lines.append(f"Last Reload At : {self.last_reload_at.isoformat()}")
        if self.last_reload_error is not None:
            redacted_error = self._redact_telegram_secrets(self.last_reload_error)
            lines.append(f"Last Reload Error : {redacted_error}")

        return "\n".join(lines)

    def _redact_telegram_secrets(self, value: str) -> str:
        """상태 메시지에서 Telegram 인증/대상 값을 제거합니다."""
        redacted = value
        telegram = self.current_settings.telegram
        secrets = [
            telegram.bot_token,
            telegram.chat_id,
            *telegram.remote_control.allowed_chat_ids,
        ]
        for secret in sorted((secret for secret in secrets if secret), key=len, reverse=True):
            redacted = redacted.replace(secret, "[redacted]")
        return redacted
