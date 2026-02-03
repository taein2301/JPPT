from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.jppt.utils.telegram import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_send_message() -> None:
    with patch("src.jppt.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(
            bot_token="test-token", chat_id="12345", enabled=True
        )
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
    with patch("src.jppt.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception("API error")
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(
            bot_token="test-token", chat_id="12345", enabled=True
        )

        # Should not raise, just log error
        await notifier.send_message("test")
