import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.utils.app_runner as app_runner
from src.utils.app_runner import run_app
from src.utils.config import Settings
from src.utils.reload import ReloadCoordinator, ReloadResult
from src.utils.telegram_remote import TelegramRemoteController


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


class _RunningShutdown(_ImmediateShutdown):
    """테스트용 실행 중 shutdown."""

    def __init__(self) -> None:
        super().__init__()
        self.should_exit = False


def _settings(*, remote_control_enabled: bool = False, bot_token: str = "test-token") -> Settings:
    """app_runner 테스트용 설정을 생성합니다."""
    remote_control = {"enabled": False}
    if remote_control_enabled:
        remote_control = {"enabled": True, "allowed_chat_ids": ["12345"]}

    return Settings(
        app={"name": "jppt", "version": "0.1.0", "debug": False},
        logging={"level": "INFO", "json_logs": False},
        telegram={
            "enabled": remote_control_enabled,
            "bot_token": bot_token if remote_control_enabled else "",
            "chat_id": "12345" if remote_control_enabled else "",
            "remote_control": remote_control,
        },
    )


def _write_remote_config(config_dir: Path, *, bot_token: str) -> None:
    """reload 테스트용 prod.yaml을 작성합니다."""
    config_dir.mkdir()
    (config_dir / "prod.yaml").write_text(
        f"""
app:
  name: "jppt"
  version: "0.1.0"
  debug: false

logging:
  level: "DEBUG"
  format: "{{time}} | {{level}} | {{message}}"
  json_logs: false
  rotation: "00:00"
  retention: "10 days"

telegram:
  enabled: true
  bot_token: "{bot_token}"
  chat_id: "12345"
  remote_control:
    enabled: true
    allowed_chat_ids:
      - "12345"
"""
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
    assert len(shutdown.cleanup_callbacks) == 1
    controller.stop.assert_awaited_once()


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


@pytest.mark.asyncio
async def test_remote_lifecycle_reload_enabled_to_disabled_stops_and_clears_controller() -> None:
    """reload로 remote_control이 꺼지면 기존 controller를 중지하고 비워야 합니다."""
    controller = MagicMock()
    controller.start = AsyncMock()
    controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with patch("src.utils.app_runner.TelegramRemoteController", return_value=controller):
        await lifecycle.apply(_settings(remote_control_enabled=True, bot_token="old-token"))
        assert lifecycle.controller is controller

        await lifecycle.apply(_settings(remote_control_enabled=False))

    controller.stop.assert_awaited_once()
    assert lifecycle.controller is None


@pytest.mark.asyncio
async def test_remote_lifecycle_reload_changed_bot_token_restarts_controller() -> None:
    """reload로 bot_token이 바뀌면 기존 controller를 멈추고 새 controller를 시작합니다."""
    old_controller = MagicMock()
    old_controller.start = AsyncMock()
    old_controller.stop = AsyncMock()
    new_controller = MagicMock()
    new_controller.start = AsyncMock()
    new_controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with patch(
        "src.utils.app_runner.TelegramRemoteController",
        side_effect=[old_controller, new_controller],
    ) as controller_class:
        await lifecycle.apply(_settings(remote_control_enabled=True, bot_token="old-token"))
        await lifecycle.apply(_settings(remote_control_enabled=True, bot_token="new-token"))

    assert controller_class.call_args_list[0].kwargs["bot_token"] == "old-token"
    assert controller_class.call_args_list[1].kwargs["bot_token"] == "new-token"
    old_controller.stop.assert_awaited_once()
    new_controller.start.assert_awaited_once()
    assert lifecycle.controller is new_controller


@pytest.mark.asyncio
async def test_remote_lifecycle_reload_same_bot_token_updates_remote_control() -> None:
    """reload 후 bot_token이 같으면 controller를 재시작하지 않고 설정만 갱신합니다."""
    controller = MagicMock()
    controller.start = AsyncMock()
    controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )
    first_settings = _settings(remote_control_enabled=True, bot_token="same-token")
    next_settings = _settings(remote_control_enabled=True, bot_token="same-token")

    with patch("src.utils.app_runner.TelegramRemoteController", return_value=controller):
        await lifecycle.apply(first_settings)
        await lifecycle.apply(next_settings)

    controller.start.assert_awaited_once()
    controller.stop.assert_not_awaited()
    controller.update_remote_control.assert_called_once_with(next_settings.telegram.remote_control)


@pytest.mark.asyncio
async def test_reload_failed_remote_restart_preserves_old_controller_and_logger(
    tmp_path: Path,
) -> None:
    """새 controller start 실패 시 reload는 실패하고 기존 controller/logger를 보존합니다."""
    config_dir = tmp_path / "config"
    _write_remote_config(config_dir, bot_token="new-token")
    old_settings = _settings(remote_control_enabled=True, bot_token="old-token")
    old_controller = MagicMock()
    old_controller.start = AsyncMock()
    old_controller.stop = AsyncMock()
    failed_controller = MagicMock()
    failed_controller.start = AsyncMock(side_effect=RuntimeError("new controller failed"))
    failed_controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with (
        patch(
            "src.utils.app_runner.TelegramRemoteController",
            side_effect=[old_controller, failed_controller],
        ),
        patch("src.utils.app_runner.setup_logger") as mock_setup_logger,
    ):
        await lifecycle.apply(old_settings)
        coordinator = ReloadCoordinator(
            settings=old_settings,
            env="prod",
            config_dir=config_dir,
            apply_settings=lambda next_settings: app_runner._apply_settings_to_runtime(
                old_settings,
                next_settings,
                remote_lifecycle=lifecycle,
                log_level=None,
                verbose=False,
            ),
        )

        result = await coordinator.reload()

    assert result.succeeded is False
    assert result.settings is old_settings
    assert coordinator.current_settings is old_settings
    assert lifecycle.controller is old_controller
    old_controller.stop.assert_not_awaited()
    failed_controller.start.assert_awaited_once()
    mock_setup_logger.assert_not_called()


@pytest.mark.asyncio
async def test_reload_failed_logger_setup_rolls_back_prepared_controller(
    tmp_path: Path,
) -> None:
    """logger 실제 적용 실패 시 준비된 새 controller를 중지하고 기존 controller를 유지합니다."""
    config_dir = tmp_path / "config"
    _write_remote_config(config_dir, bot_token="new-token")
    old_settings = _settings(remote_control_enabled=True, bot_token="old-token")
    old_controller = MagicMock()
    old_controller.start = AsyncMock()
    old_controller.stop = AsyncMock()
    new_controller = MagicMock()
    new_controller.start = AsyncMock()
    new_controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with (
        patch(
            "src.utils.app_runner.TelegramRemoteController",
            side_effect=[old_controller, new_controller],
        ) as controller_class,
        patch("src.utils.app_runner.setup_logger", side_effect=RuntimeError("setup failed"))
        as mock_setup_logger,
    ):
        await lifecycle.apply(old_settings)
        coordinator = ReloadCoordinator(
            settings=old_settings,
            env="prod",
            config_dir=config_dir,
            apply_settings=lambda next_settings: app_runner._apply_settings_to_runtime(
                old_settings,
                next_settings,
                remote_lifecycle=lifecycle,
                log_level=None,
                verbose=False,
            ),
        )

        result = await coordinator.reload()

    assert result.succeeded is False
    assert result.settings is old_settings
    assert coordinator.current_settings is old_settings
    assert lifecycle.controller is old_controller
    old_controller.stop.assert_not_awaited()
    new_controller.start.assert_awaited_once()
    new_controller.stop.assert_awaited_once()
    assert controller_class.call_count == 2
    mock_setup_logger.assert_called_once()


@pytest.mark.asyncio
async def test_reload_failed_logger_validation_preserves_old_controller(
    tmp_path: Path,
) -> None:
    """logger 검증 실패 시 새 controller로 교체하지 않고 기존 상태를 유지합니다."""
    config_dir = tmp_path / "config"
    _write_remote_config(config_dir, bot_token="new-token")
    old_settings = _settings(remote_control_enabled=True, bot_token="old-token")
    old_controller = MagicMock()
    old_controller.start = AsyncMock()
    old_controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with (
        patch("src.utils.app_runner.TelegramRemoteController", return_value=old_controller)
        as controller_class,
        patch(
            "src.utils.app_runner.validate_logger_config",
            side_effect=ValueError("bad logger config"),
        ) as mock_validate_logger_config,
        patch("src.utils.app_runner.setup_logger") as mock_setup_logger,
    ):
        await lifecycle.apply(old_settings)
        coordinator = ReloadCoordinator(
            settings=old_settings,
            env="prod",
            config_dir=config_dir,
            apply_settings=lambda next_settings: app_runner._apply_settings_to_runtime(
                old_settings,
                next_settings,
                remote_lifecycle=lifecycle,
                log_level=None,
                verbose=False,
            ),
        )

        result = await coordinator.reload()

    assert result.succeeded is False
    assert result.settings is old_settings
    assert coordinator.current_settings is old_settings
    assert lifecycle.controller is old_controller
    old_controller.stop.assert_not_awaited()
    assert controller_class.call_count == 1
    mock_validate_logger_config.assert_called_once()
    mock_setup_logger.assert_not_called()


@pytest.mark.asyncio
async def test_reload_handler_defers_current_controller_stop_until_after_reply() -> None:
    """현재 Telegram handler의 controller stop은 응답 이후 background로 지연합니다."""
    events: list[str] = []
    old_settings = _settings(remote_control_enabled=True, bot_token="old-token")
    next_settings = _settings(remote_control_enabled=False)
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    async def reload_callback() -> ReloadResult:
        await lifecycle.apply(next_settings)
        return ReloadResult(succeeded=True, message="reload ok", settings=next_settings)

    controller = TelegramRemoteController(
        bot_token="old-token",
        remote_control=old_settings.telegram.remote_control,
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )

    async def stop_controller() -> None:
        events.append("stop")

    async def reply_text(message: str) -> None:
        assert message == "reload ok"
        events.append("reply")

    controller.stop = AsyncMock(side_effect=stop_controller)  # type: ignore[method-assign]
    lifecycle.controller = controller
    lifecycle._bot_token = "old-token"

    update = MagicMock()
    update.effective_chat.id = 12345
    update.effective_message.reply_text = AsyncMock(side_effect=reply_text)

    await controller.handle_reload(update, MagicMock())

    assert events == ["reply"]
    assert lifecycle.controller is None

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert events == ["reply", "stop"]
    controller.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_reload_handler_defers_old_controller_stop_on_token_change() -> None:
    """bot_token 변경 reload도 응답 이후 기존 controller를 background로 중지합니다."""
    events: list[str] = []
    old_settings = _settings(remote_control_enabled=True, bot_token="old-token")
    next_settings = _settings(remote_control_enabled=True, bot_token="new-token")
    new_controller = MagicMock()
    new_controller.start = AsyncMock()
    new_controller.stop = AsyncMock()
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    async def reload_callback() -> ReloadResult:
        with patch("src.utils.app_runner.TelegramRemoteController", return_value=new_controller):
            await lifecycle.apply(next_settings)
        return ReloadResult(succeeded=True, message="reload ok", settings=next_settings)

    old_controller = TelegramRemoteController(
        bot_token="old-token",
        remote_control=old_settings.telegram.remote_control,
        reload_callback=reload_callback,
        status_callback=lambda: "status",
    )

    async def stop_old_controller() -> None:
        events.append("stop-old")

    async def reply_text(message: str) -> None:
        assert message == "reload ok"
        events.append("reply")

    old_controller.stop = AsyncMock(side_effect=stop_old_controller)  # type: ignore[method-assign]
    lifecycle.controller = old_controller
    lifecycle._bot_token = "old-token"

    update = MagicMock()
    update.effective_chat.id = 12345
    update.effective_message.reply_text = AsyncMock(side_effect=reply_text)

    await old_controller.handle_reload(update, MagicMock())

    assert events == ["reply"]
    assert lifecycle.controller is new_controller
    new_controller.start.assert_awaited_once()

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert events == ["reply", "stop-old"]
    old_controller.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_remote_lifecycle_stop_failure_keeps_controller_handle() -> None:
    """stop 실패 시 controller handle을 먼저 지우면 이후 복구가 불가능합니다."""
    controller = MagicMock()
    controller.start = AsyncMock()
    controller.stop = AsyncMock(side_effect=RuntimeError("stop failed"))
    lifecycle = app_runner._RemoteControllerLifecycle(
        reload_callback=AsyncMock(),
        status_callback=lambda: "status",
    )

    with patch("src.utils.app_runner.TelegramRemoteController", return_value=controller):
        await lifecycle.apply(_settings(remote_control_enabled=True, bot_token="old-token"))
        with pytest.raises(RuntimeError, match="stop failed"):
            await lifecycle.apply(_settings(remote_control_enabled=False))

    assert lifecycle.controller is controller


@pytest.mark.asyncio
async def test_run_app_exception_stops_remote_controller() -> None:
    """앱 루프 예외 종료에서도 remote controller를 중지해야 합니다."""
    settings = _settings(remote_control_enabled=True)
    shutdown = _RunningShutdown()
    controller = MagicMock()
    controller.start = AsyncMock()
    controller.stop = AsyncMock()

    async def raise_runtime_error(seconds: int) -> None:
        del seconds
        raise RuntimeError("loop failed")

    with (
        patch("src.utils.app_runner.GracefulShutdown", return_value=shutdown),
        patch("src.utils.app_runner.setup_signal_handlers"),
        patch("src.utils.app_runner.asyncio.sleep", side_effect=raise_runtime_error),
        patch("src.utils.app_runner.TelegramNotifier.send_message", new_callable=AsyncMock),
        patch("src.utils.app_runner.TelegramRemoteController", return_value=controller),
        pytest.raises(RuntimeError, match="loop failed"),
    ):
        await run_app(settings, "prod")

    controller.stop.assert_awaited_once()
