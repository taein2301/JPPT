"""장시간 실행되는 데몬을 위한 앱 모드 실행기.

이 모듈은 시그널 처리와 graceful shutdown을 지원하는 앱 모드 실행을 담당합니다.
"""

import asyncio
from pathlib import Path

from loguru import logger

from src.utils.config import Settings
from src.utils.logger import setup_logger
from src.utils.reload import ReloadCoordinator
from src.utils.signals import GracefulShutdown, setup_signal_handlers
from src.utils.telegram import TelegramNotifier
from src.utils.telegram_remote import TelegramRemoteController


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
        templates=settings.telegram.templates,
    )


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
    controller: TelegramRemoteController | None = None

    async def apply_settings(next_settings: Settings) -> None:
        """reload된 설정을 현재 런타임 리소스에 적용합니다."""
        nonlocal current_settings, notifier

        effective_log_level = _resolve_log_level(
            next_settings.logging.level,
            log_level,
            verbose,
        )
        setup_logger(
            level=effective_log_level,
            log_file=_build_log_file(next_settings.app.name),
            format_str=next_settings.logging.format,
            json_logs=next_settings.logging.json_logs,
            rotation=next_settings.logging.rotation,
            retention=next_settings.logging.retention,
        )
        current_settings = next_settings
        notifier = _build_notifier(current_settings)
        if controller is not None:
            controller.update_remote_control(current_settings.telegram.remote_control)

    coordinator = ReloadCoordinator(
        settings=current_settings,
        env=env,
        config_dir=config_dir,
        apply_settings=apply_settings,
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
            controller = TelegramRemoteController(
                bot_token=current_settings.telegram.bot_token,
                remote_control=current_settings.telegram.remote_control,
                reload_callback=coordinator.reload,
                status_callback=coordinator.status_message,
            )
            await controller.start()
            shutdown.register_cleanup(controller.stop)

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
        # 에러 알림
        await notifier.send_error(e, context="App mode crashed")
        raise
