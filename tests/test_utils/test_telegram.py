from datetime import datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest
from telegram.error import TimedOut

from src.utils.config import TelegramMessageTemplateConfig, TelegramSilentTimeConfig
from src.utils.telegram import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_send_message() -> None:
    with (
        patch("src.utils.telegram.Bot") as mock_bot_class,
        patch("src.utils.telegram.logger.info") as mock_info,
    ):
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        await notifier.send_message("test message")

        mock_bot.send_message.assert_called_once_with(
            chat_id="12345", text="test message", parse_mode=None
        )
        assert any(
            "Telegram message sent to {} message={}" == str(call.args[0])
            and call.args[1] == "12345"
            and call.args[2] == "test message"
            for call in mock_info.call_args_list
        )


@pytest.mark.asyncio
async def test_telegram_disabled() -> None:
    notifier = TelegramNotifier(bot_token="", chat_id="", enabled=False)
    # Should not raise error
    await notifier.send_message("test")


@pytest.mark.asyncio
async def test_telegram_error_handling() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception("API error")
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)

        # Should not raise, just log error
        await notifier.send_message("test")


@pytest.mark.asyncio
async def test_telegram_timeout_is_warning_not_error() -> None:
    with (
        patch("src.utils.telegram.Bot") as mock_bot_class,
        patch("src.utils.telegram.logger.warning") as mock_warning,
        patch("src.utils.telegram.logger.error") as mock_error,
    ):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TimedOut("Timed out")
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        await notifier.send_message("test")

    mock_warning.assert_called_once()
    mock_error.assert_not_called()


@pytest.mark.asyncio
async def test_telegram_send_message_skipped_during_silent_time() -> None:
    with (
        patch("src.utils.telegram.Bot") as mock_bot_class,
        patch("src.utils.telegram.logger.info") as mock_info,
    ):
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        notifier = TelegramNotifier(
            bot_token="test-token",
            chat_id="12345",
            enabled=True,
            silent_time=TelegramSilentTimeConfig(
                enabled=True,
                start="23:00",
                end="08:00",
                timezone="Asia/Seoul",
            ),
            now_provider=lambda: datetime(2026, 3, 14, 23, 30, tzinfo=ZoneInfo("Asia/Seoul")),
        )

        result = await notifier.send_message("test message")

    assert result is False
    mock_bot.send_message.assert_not_called()
    assert any(
        "Telegram notification skipped due to silent time: {}-{} ({}) message={}"
        == str(call.args[0])
        and call.args[4] == "test message"
        for call in mock_info.call_args_list
    )


@pytest.mark.asyncio
async def test_telegram_send_message_allows_outside_silent_time() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        notifier = TelegramNotifier(
            bot_token="test-token",
            chat_id="12345",
            enabled=True,
            silent_time=TelegramSilentTimeConfig(
                enabled=True,
                start="23:00",
                end="08:00",
                timezone="Asia/Seoul",
            ),
            now_provider=lambda: datetime(2026, 3, 14, 12, 0, tzinfo=ZoneInfo("Asia/Seoul")),
        )

        result = await notifier.send_message("test message")

    assert result is True
    mock_bot.send_message.assert_called_once_with(
        chat_id="12345", text="test message", parse_mode=None
    )


@pytest.mark.asyncio
async def test_telegram_send_template_renders_message() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        result = await notifier.send_template("안녕하세요 {name}", name="JPPT")

    assert result is True
    mock_bot.send_message.assert_called_once_with(
        chat_id="12345", text="안녕하세요 JPPT", parse_mode=None
    )


@pytest.mark.asyncio
async def test_telegram_send_template_returns_false_when_missing_key() -> None:
    with (
        patch("src.utils.telegram.Bot") as mock_bot_class,
        patch("src.utils.telegram.logger.error") as mock_error,
    ):
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        result = await notifier.send_template("안녕하세요 {name}")

    assert result is False
    mock_error.assert_called_once()
    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_telegram_send_error_uses_template() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        notifier = TelegramNotifier(
            bot_token="test-token",
            chat_id="12345",
            enabled=True,
            templates=TelegramMessageTemplateConfig(
                error_alert="에러={error_type}, 메시지={error_message}, 컨텍스트={context}"
            ),
        )

        result = await notifier.send_error(ValueError("실패"), context="배치 실행")

    assert result is True
    mock_bot.send_message.assert_called_once_with(
        chat_id="12345",
        text="에러=ValueError, 메시지=실패, 컨텍스트=배치 실행",
        parse_mode=None,
    )


def test_format_status_message_with_env() -> None:
    message = TelegramNotifier.format_status_message("j-upbit", "start", env="prod")
    assert message == "[J-UPBIT] 🚀 start\nEnv : prod"


def test_format_status_message_with_reason() -> None:
    message = TelegramNotifier.format_status_message("j-upbit", "stop", reason="gracefully")
    assert message == "[J-UPBIT] 🛑 stop\nReason : gracefully"


def test_format_status_message_wraps_unbracketed_app_name() -> None:
    message = TelegramNotifier.format_status_message("j-bithumb", "start", env="dev")
    assert message == "[J-BITHUMB] 🚀 start\nEnv : dev"


def test_format_status_message_with_batch_status() -> None:
    message = TelegramNotifier.format_status_message("j-upbit", "batch completed", reason="done")
    assert message == "[J-UPBIT] ✅ batch completed\nReason : done"
