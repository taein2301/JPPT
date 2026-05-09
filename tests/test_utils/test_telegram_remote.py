"""Telegram 원격제어 명령 처리 테스트."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.utils.config import TelegramRemoteControlConfig
from src.utils.reload import ReloadResult
from src.utils.telegram_remote import TelegramRemoteController


def _remote_control(
    *,
    enabled: bool = True,
    allowed_chat_ids: list[str] | None = None,
    reload_enabled: bool = True,
    status_enabled: bool = True,
    help_enabled: bool = True,
) -> TelegramRemoteControlConfig:
    """테스트용 원격제어 설정을 생성합니다."""
    return TelegramRemoteControlConfig(
        enabled=enabled,
        allowed_chat_ids=allowed_chat_ids or ["12345"],
        commands={
            "reload": reload_enabled,
            "status": status_enabled,
            "help": help_enabled,
        },
    )


def _update(chat_id: int | str) -> SimpleNamespace:
    """CommandHandler에 전달할 최소 update 객체를 생성합니다."""
    reply_text = AsyncMock()
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        effective_message=SimpleNamespace(reply_text=reply_text),
    )


def _telegram_application() -> SimpleNamespace:
    """테스트용 python-telegram-bot Application 대역을 생성합니다."""
    updater = SimpleNamespace(
        start_polling=AsyncMock(),
        stop=AsyncMock(),
    )
    return SimpleNamespace(
        add_handler=Mock(),
        initialize=AsyncMock(),
        start=AsyncMock(),
        stop=AsyncMock(),
        shutdown=AsyncMock(),
        updater=updater,
        running=True,
    )


@pytest.mark.asyncio
async def test_unauthorized_reload_does_not_call_callback_or_reply() -> None:
    """허용되지 않은 chat id의 reload는 콜백과 응답을 모두 건너뛰어야 한다."""
    reload_callback = AsyncMock()
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(allowed_chat_ids=["12345"]),
        reload_callback=reload_callback,
        status_callback=Mock(return_value="status"),
    )
    update = _update("99999")

    await controller.handle_reload(update, SimpleNamespace())

    reload_callback.assert_not_awaited()
    update.effective_message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorized_reload_calls_callback_and_replies_with_result_message() -> None:
    """허용된 reload는 콜백 결과 메시지를 그대로 응답해야 한다."""
    result = ReloadResult(succeeded=True, message="reload ok", settings=Mock())
    reload_callback = AsyncMock(return_value=result)
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(allowed_chat_ids=["12345"]),
        reload_callback=reload_callback,
        status_callback=Mock(return_value="status"),
    )
    update = _update(12345)

    await controller.handle_reload(update, SimpleNamespace())

    reload_callback.assert_awaited_once_with()
    update.effective_message.reply_text.assert_awaited_once_with("reload ok")


@pytest.mark.asyncio
async def test_disabled_reload_command_replies_disabled_and_does_not_call_callback() -> None:
    """reload 명령이 꺼져 있으면 disabled 메시지만 응답해야 한다."""
    reload_callback = AsyncMock()
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(reload_enabled=False),
        reload_callback=reload_callback,
        status_callback=Mock(return_value="status"),
    )
    update = _update("12345")

    await controller.handle_reload(update, SimpleNamespace())

    reload_callback.assert_not_awaited()
    update.effective_message.reply_text.assert_awaited_once_with("reload command disabled")


@pytest.mark.asyncio
async def test_status_replies_with_status_callback_output_and_does_not_reload() -> None:
    """status 명령은 status 콜백 결과만 응답해야 한다."""
    reload_callback = AsyncMock()
    status_callback = Mock(return_value="current status")
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(),
        reload_callback=reload_callback,
        status_callback=status_callback,
    )
    update = _update("12345")

    await controller.handle_status(update, SimpleNamespace())

    status_callback.assert_called_once_with()
    reload_callback.assert_not_awaited()
    update.effective_message.reply_text.assert_awaited_once_with("current status")


@pytest.mark.asyncio
async def test_help_lists_only_enabled_commands_in_order() -> None:
    """help는 모든 명령이 켜졌을 때 고정 순서로 나열해야 한다."""
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(),
        reload_callback=AsyncMock(),
        status_callback=Mock(return_value="status"),
    )
    update = _update("12345")

    await controller.handle_help(update, SimpleNamespace())

    update.effective_message.reply_text.assert_awaited_once_with(
        "Commands:\n/reload\n/status\n/help"
    )


@pytest.mark.asyncio
async def test_help_omits_disabled_status_command() -> None:
    """help는 꺼진 status 명령을 제외하고 켜진 명령만 나열해야 한다."""
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(status_enabled=False),
        reload_callback=AsyncMock(),
        status_callback=Mock(return_value="status"),
    )
    update = _update("12345")

    await controller.handle_help(update, SimpleNamespace())

    update.effective_message.reply_text.assert_awaited_once_with("Commands:\n/reload\n/help")


def test_update_remote_control_replaces_allowed_chat_ids() -> None:
    """update_remote_control은 허용 chat id 목록을 새 설정으로 교체해야 한다."""
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(allowed_chat_ids=["11111"]),
        reload_callback=AsyncMock(),
        status_callback=Mock(return_value="status"),
    )

    controller.update_remote_control(_remote_control(allowed_chat_ids=["22222"]))

    assert controller.is_chat_allowed("11111") is False
    assert controller.is_chat_allowed("22222") is True


@pytest.mark.asyncio
async def test_start_and_stop_manage_application_lifecycle() -> None:
    """start/stop은 PTB application lifecycle 메서드를 수동 순서로 호출해야 한다."""
    application = _telegram_application()
    builder = Mock()
    builder.token.return_value = builder
    builder.build.return_value = application
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(),
        reload_callback=AsyncMock(),
        status_callback=Mock(return_value="status"),
    )

    with patch("src.utils.telegram_remote.ApplicationBuilder", return_value=builder):
        await controller.start()

    builder.token.assert_called_once_with("token")
    builder.build.assert_called_once_with()
    assert application.add_handler.call_count == 3
    application.initialize.assert_awaited_once_with()
    application.start.assert_awaited_once_with()
    application.updater.start_polling.assert_awaited_once_with()
    assert controller.application is application

    await controller.stop()

    application.updater.stop.assert_awaited_once_with()
    application.stop.assert_awaited_once_with()
    application.shutdown.assert_awaited_once_with()
    assert controller.application is None


@pytest.mark.asyncio
async def test_start_cleans_up_application_when_polling_start_fails() -> None:
    """polling 시작 실패 시 시작된 application을 정리하고 예외를 다시 던져야 한다."""
    application = _telegram_application()
    application.updater.start_polling.side_effect = RuntimeError("polling failed")
    builder = Mock()
    builder.token.return_value = builder
    builder.build.return_value = application
    controller = TelegramRemoteController(
        bot_token="token",
        remote_control=_remote_control(),
        reload_callback=AsyncMock(),
        status_callback=Mock(return_value="status"),
    )

    with (
        patch("src.utils.telegram_remote.ApplicationBuilder", return_value=builder),
        pytest.raises(RuntimeError, match="polling failed"),
    ):
        await controller.start()

    application.initialize.assert_awaited_once_with()
    application.start.assert_awaited_once_with()
    application.updater.start_polling.assert_awaited_once_with()
    application.stop.assert_awaited_once_with()
    application.shutdown.assert_awaited_once_with()
    assert controller.application is None
