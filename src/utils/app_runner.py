"""장시간 실행되는 데몬을 위한 앱 모드 실행기.

이 모듈은 시그널 처리와 graceful shutdown을 지원하는 앱 모드 실행을 담당합니다.
"""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from loguru import logger

from src.utils.config import Settings, TelegramRemoteControlConfig
from src.utils.logger import setup_logger, validate_logger_config
from src.utils.reload import ReloadCoordinator, ReloadResult
from src.utils.signals import GracefulShutdown, setup_signal_handlers
from src.utils.telegram import TelegramNotifier
from src.utils.telegram_remote import TelegramRemoteController, defer_reload_cleanup

_RemoteChangeAction = Literal["stop", "start", "restart", "update"]


def _build_log_file(app_name: str) -> Path:
    """앱 모드 로그 파일 경로를 생성합니다."""
    return Path.home() / "logs" / f"{app_name}.log"


def _resolve_log_level(config_level: str, log_level: str | None, verbose: bool) -> str:
    """CLI 옵션과 설정 파일을 조합해 최종 로그 레벨을 결정합니다."""
    if verbose:
        return "DEBUG"
    if log_level:
        return log_level.upper()
    return config_level


def _build_notifier(settings: Settings) -> TelegramNotifier:
    """현재 설정으로 Telegram notifier를 생성합니다."""
    return TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        enabled=settings.telegram.enabled,
        silent_time=settings.telegram.silent_time,
    )


class _RemoteControllerLifecycle:
    """Telegram remote controller의 시작/갱신/중지를 관리합니다."""

    def __init__(
        self,
        *,
        reload_callback: Callable[[], Awaitable[ReloadResult]],
        status_callback: Callable[[], str],
    ) -> None:
        """lifecycle 관리자를 초기화합니다."""
        self.reload_callback = reload_callback
        self.status_callback = status_callback
        self.controller: TelegramRemoteController | None = None
        self._bot_token: str | None = None

    async def apply(self, settings: Settings) -> None:
        """설정에 맞게 remote controller 상태를 반영합니다."""
        change = await self.prepare(settings)
        await change.commit()

    async def prepare(self, settings: Settings) -> "_PreparedRemoteControllerChange":
        """controller 교체 작업을 준비하되 기존 controller는 아직 유지합니다."""
        remote_control = settings.telegram.remote_control
        if not remote_control.enabled:
            return _PreparedRemoteControllerChange(
                lifecycle=self,
                settings=settings,
                action="stop",
            )

        bot_token = settings.telegram.bot_token
        if self.controller is None:
            new_controller = self._build_controller(settings)
            await new_controller.start()
            return _PreparedRemoteControllerChange(
                lifecycle=self,
                settings=settings,
                action="start",
                new_controller=new_controller,
            )

        if self._bot_token != bot_token:
            new_controller = self._build_controller(settings)
            await new_controller.start()
            return _PreparedRemoteControllerChange(
                lifecycle=self,
                settings=settings,
                action="restart",
                new_controller=new_controller,
            )

        return _PreparedRemoteControllerChange(
            lifecycle=self,
            settings=settings,
            action="update",
        )

    async def stop(self) -> None:
        """실행 중인 remote controller를 중지하고 상태를 비웁니다."""
        if self.controller is None:
            return

        controller = self.controller
        await controller.stop()
        self.controller = None
        self._bot_token = None

    def _build_controller(self, settings: Settings) -> TelegramRemoteController:
        """현재 설정으로 remote controller 객체를 생성합니다."""
        return TelegramRemoteController(
            bot_token=settings.telegram.bot_token,
            remote_control=settings.telegram.remote_control,
            reload_callback=self.reload_callback,
            status_callback=self.status_callback,
        )


class _PreparedRemoteControllerChange:
    """준비된 remote controller 변경을 commit/rollback합니다."""

    def __init__(
        self,
        *,
        lifecycle: _RemoteControllerLifecycle,
        settings: Settings,
        action: _RemoteChangeAction,
        new_controller: TelegramRemoteController | None = None,
    ) -> None:
        """준비된 변경 객체를 초기화합니다."""
        self.lifecycle = lifecycle
        self.settings = settings
        self.action = action
        self.new_controller = new_controller

    async def commit(self) -> None:
        """준비된 변경을 현재 lifecycle에 확정합니다."""
        if self.action == "stop":
            await self._stop_current_controller()
            return

        if self.action == "update":
            if self.lifecycle.controller is not None:
                self.lifecycle.controller.update_remote_control(
                    self.settings.telegram.remote_control
                )
            return

        if self.new_controller is None:
            raise RuntimeError("prepared remote controller is missing")

        if self.action == "restart" and self.lifecycle.controller is not None:
            await self._stop_current_controller()

        self.lifecycle.controller = self.new_controller
        self.lifecycle._bot_token = self.settings.telegram.bot_token
        self.new_controller = None

    async def _stop_current_controller(self) -> None:
        """현재 controller를 멈추거나 `/reload` 응답 이후로 지연합니다."""
        controller = self.lifecycle.controller
        if controller is None:
            return

        if defer_reload_cleanup(controller.stop):
            controller.update_remote_control(TelegramRemoteControlConfig(enabled=False))
            self.lifecycle.controller = None
            self.lifecycle._bot_token = None
            return

        await self.lifecycle.stop()

    async def rollback(self) -> None:
        """준비 중 시작한 새 controller가 있으면 정리합니다."""
        if self.new_controller is None:
            return

        try:
            await self.new_controller.stop()
        except Exception as cleanup_error:  # noqa: BLE001 - 원래 실패를 유지합니다.
            logger.error(f"Prepared remote controller cleanup failed: {cleanup_error}")
        finally:
            self.new_controller = None


async def _apply_settings_to_runtime(
    current_settings: Settings,
    next_settings: Settings,
    *,
    remote_lifecycle: _RemoteControllerLifecycle,
    log_level: str | None,
    verbose: bool,
) -> TelegramNotifier:
    """reload된 설정을 remote controller와 logger/notifier에 적용합니다."""
    effective_log_level = _resolve_log_level(
        next_settings.logging.level,
        log_level,
        verbose,
    )
    log_file = _build_log_file(next_settings.app.name)
    validate_logger_config(
        level=effective_log_level,
        log_file=log_file,
        format_str=next_settings.logging.format,
        json_logs=next_settings.logging.json_logs,
        rotation=next_settings.logging.rotation,
        retention=next_settings.logging.retention,
    )
    change = await remote_lifecycle.prepare(next_settings)
    logger_applied = False
    try:
        setup_logger(
            level=effective_log_level,
            log_file=log_file,
            format_str=next_settings.logging.format,
            json_logs=next_settings.logging.json_logs,
            rotation=next_settings.logging.rotation,
            retention=next_settings.logging.retention,
        )
        logger_applied = True
        next_notifier = _build_notifier(next_settings)
        await change.commit()
    except Exception:
        await change.rollback()
        if logger_applied:
            current_log_level = _resolve_log_level(
                current_settings.logging.level,
                log_level,
                verbose,
            )
            try:
                setup_logger(
                    level=current_log_level,
                    log_file=_build_log_file(current_settings.app.name),
                    format_str=current_settings.logging.format,
                    json_logs=current_settings.logging.json_logs,
                    rotation=current_settings.logging.rotation,
                    retention=current_settings.logging.retention,
                )
            except Exception as restore_error:  # noqa: BLE001 - 원래 실패를 유지합니다.
                logger.error(f"Logger restore after failed reload failed: {restore_error}")
        raise

    return next_notifier


async def run_app(
    settings: Settings,
    env: str,
    *,
    config_dir: Path | None = None,
    log_level: str | None = None,
    verbose: bool = False,
) -> None:
    """앱 모드를 실행합니다 (graceful shutdown 지원 데몬).

    이 함수는 템플릿 구현입니다. 실제 비즈니스 로직으로 교체하세요.

    Args:
        settings: 애플리케이션 설정
        env: 실행 환경 이름

    사용 예시:
        async def run_app(settings: Settings, env: str) -> None:
            shutdown = GracefulShutdown()
            setup_signal_handlers(shutdown)

            async def cleanup() -> None:
                logger.info("리소스 정리 중")
                await close_connections()

            shutdown.register_cleanup(cleanup)

            async with shutdown:
                while not shutdown.should_exit:
                    await process_iteration()
                    await asyncio.sleep(1)
    """
    logger.info("App mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    current_settings = settings
    notifier = _build_notifier(current_settings)
    remote_lifecycle: _RemoteControllerLifecycle

    async def apply_settings(next_settings: Settings) -> None:
        """reload된 설정을 현재 런타임 리소스에 적용합니다."""
        nonlocal current_settings, notifier

        next_notifier = await _apply_settings_to_runtime(
            current_settings,
            next_settings,
            remote_lifecycle=remote_lifecycle,
            log_level=log_level,
            verbose=verbose,
        )
        current_settings = next_settings
        notifier = next_notifier

    coordinator = ReloadCoordinator(
        settings=current_settings,
        env=env,
        config_dir=config_dir,
        apply_settings=apply_settings,
    )
    remote_lifecycle = _RemoteControllerLifecycle(
        reload_callback=coordinator.reload,
        status_callback=coordinator.status_message,
    )

    # 시작 알림 전송
    await notifier.send_message(
        TelegramNotifier.format_status_message(
            current_settings.app.name,
            "start",
            env=env,
        )
    )

    # Graceful shutdown 설정
    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)

    try:
        if current_settings.telegram.remote_control.enabled:
            await remote_lifecycle.apply(current_settings)
            shutdown.register_cleanup(remote_lifecycle.stop)

        async with shutdown:
            logger.info("App running (Press Ctrl+C to stop)")

            # TODO: 메인 루프 구현
            iteration = 0
            while not shutdown.should_exit:
                iteration += 1
                logger.debug(f"App iteration {iteration}")
                await asyncio.sleep(5)  # 실제 로직으로 교체

        logger.info("App mode stopped")
        # 정상 종료 알림
        await notifier.send_message(
            TelegramNotifier.format_status_message(
                current_settings.app.name,
                "stop",
                reason="gracefully",
            )
        )
    except Exception as e:
        logger.error(f"App crashed: {e}")
        raise
    finally:
        try:
            await remote_lifecycle.stop()
        except Exception as e:  # noqa: BLE001 - cleanup 실패는 원래 종료 흐름을 가리지 않습니다.
            logger.error(f"Remote controller cleanup failed: {e}")
