"""Telegram notification integration."""

from loguru import logger
from telegram import Bot
from telegram.error import TelegramError

from src.jppt.utils.exceptions import TelegramError as TelegramException


class TelegramNotifier:
    """
    Send notifications via Telegram.

    Example:
        notifier = TelegramNotifier(bot_token="xxx", chat_id="yyy", enabled=True)
        await notifier.send_message("Hello!")
    """

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True) -> None:
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled
        self.chat_id = chat_id
        self._bot: Bot | None = None

        if enabled and bot_token:
            self._bot = Bot(token=bot_token)
            logger.info(f"Telegram notifier initialized: chat_id={chat_id}")
        elif enabled:
            logger.warning("Telegram enabled but bot_token is empty")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
    ) -> None:
        """
        Send message to Telegram.

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown, HTML)

        Raises:
            TelegramException: If sending fails (only when enabled)
        """
        if not self.enabled or not self._bot:
            logger.debug("Telegram notification skipped (disabled)")
            return

        try:
            await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            logger.info(f"Telegram message sent to {self.chat_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            # Don't raise, just log - notifications shouldn't break the app

    async def send_error(self, error: Exception, context: str = "") -> None:
        """
        Send error notification to Telegram.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        message = f"🚨 **Error Alert**\n\n"
        if context:
            message += f"**Context:** {context}\n\n"
        message += f"**Error:** `{type(error).__name__}`\n"
        message += f"**Message:** {str(error)}"

        await self.send_message(message)
