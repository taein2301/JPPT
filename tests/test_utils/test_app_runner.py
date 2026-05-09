from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.app_runner import run_app
from src.utils.config import Settings


class _ImmediateShutdown:
    """테스트용 즉시 종료 shutdown."""

    def __init__(self) -> None:
        self.should_exit = True
        self.cleanup_callbacks: list[Callable[[], Awaitable[None]]] = []

    def register_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
        self.cleanup_callbacks.append(callback)

    async def __aenter__(self) -> "_ImmediateShutdown":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def _settings(*, remote_control_enabled: bool = False) -> Settings:
    """app_runner 테스트용 설정을 생성합니다."""
    remote_control = {"enabled": False}
    if remote_control_enabled:
        remote_control = {"enabled": True, "allowed_chat_ids": ["12345"]}

    return Settings(
        app={"name": "jppt", "version": "0.1.0", "debug": False},
        logging={"level": "INFO", "json_logs": False},
        telegram={
            "enabled": remote_control_enabled,
            "bot_token": "test-token" if remote_control_enabled else "",
            "chat_id": "12345" if remote_control_enabled else "",
            "remote_control": remote_control,
        },
    )


@pytest.mark.asyncio
async def test_run_app_shutdown() -> None:
    settings = Settings()
    shutdown = _ImmediateShutdown()

    # Mock the shutdown to exit immediately
    with (
        patch("src.utils.app_runner.GracefulShutdown", return_value=shutdown),
        patch("src.utils.app_runner.setup_signal_handlers"),
        patch(
            "src.utils.app_runner.TelegramNotifier.send_message",
            new_callable=AsyncMock,
        ) as mock_send,
    ):
        # Should exit quickly
        await run_app(settings, "prod")

    assert mock_send.await_args_list[0].args[0] == "[JPPT] 🚀 start\nEnv : prod"
    assert mock_send.await_args_list[1].args[0] == "[JPPT] 🛑 stop\nReason : gracefully"


@pytest.mark.asyncio
async def test_run_app_starts_remote_controller_and_registers_cleanup() -> None:
    """remote_control이 활성화되면 컨트롤러를 시작하고 shutdown cleanup을 등록합니다."""
    settings = _settings(remote_control_enabled=True)
    shutdown = _ImmediateShutdown()
    controller = MagicMock()
    controller.start = AsyncMock()
    controller.stop = AsyncMock()

    with (
        patch("src.utils.app_runner.GracefulShutdown", return_value=shutdown),
        patch("src.utils.app_runner.setup_signal_handlers"),
        patch(
            "src.utils.app_runner.TelegramNotifier.send_message",
            new_callable=AsyncMock,
        ),
        patch("src.utils.app_runner.TelegramRemoteController") as controller_class,
    ):
        controller_class.return_value = controller

        await run_app(settings, "prod", config_dir=None, log_level="ERROR", verbose=False)

    controller_class.assert_called_once()
    call_kwargs = controller_class.call_args.kwargs
    assert call_kwargs["bot_token"] == "test-token"
    assert call_kwargs["remote_control"] == settings.telegram.remote_control
    assert callable(call_kwargs["reload_callback"])
    assert callable(call_kwargs["status_callback"])
    controller.start.assert_awaited_once()
    assert shutdown.cleanup_callbacks == [controller.stop]


@pytest.mark.asyncio
async def test_run_app_does_not_create_remote_controller_when_disabled() -> None:
    """remote_control이 비활성화되면 컨트롤러를 만들지 않습니다."""
    settings = _settings(remote_control_enabled=False)
    shutdown = _ImmediateShutdown()

    with (
        patch("src.utils.app_runner.GracefulShutdown", return_value=shutdown),
        patch("src.utils.app_runner.setup_signal_handlers"),
        patch(
            "src.utils.app_runner.TelegramNotifier.send_message",
            new_callable=AsyncMock,
        ),
        patch("src.utils.app_runner.TelegramRemoteController") as controller_class,
    ):
        await run_app(settings, "prod")

    controller_class.assert_not_called()
    assert shutdown.cleanup_callbacks == []
