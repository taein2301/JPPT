from datetime import datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest
from telegram.error import TimedOut

from src.utils.config import TelegramSilentTimeConfig
from src.utils.telegram import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_send_message() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        await notifier.send_message("test message")

        mock_bot.send_message.assert_called_once_with(
            chat_id="12345", text="test message", parse_mode="Markdown"
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
            now_provider=lambda: datetime(2026, 3, 14, 23, 30, tzinfo=ZoneInfo("Asia/Seoul")),
        )

        result = await notifier.send_message("test message")

    assert result is False
    mock_bot.send_message.assert_not_called()


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
        chat_id="12345", text="test message", parse_mode="Markdown"
    )
