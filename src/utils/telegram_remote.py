"""Telegram 원격제어 명령 처리.

이 모듈은 Telegram CommandHandler를 통해 설정 reload/status/help 명령을 처리합니다.
앱 실행 흐름에 붙이는 작업은 별도 wiring 단계에서 수행합니다.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from src.utils.config import TelegramRemoteControlConfig
from src.utils.reload import ReloadResult

ReloadCallback = Callable[[], Awaitable[ReloadResult]]
StatusCallback = Callable[[], str]


class TelegramRemoteController:
    """Telegram 명령 기반 원격제어 컨트롤러."""

    def __init__(
        self,
        *,
        bot_token: str,
        remote_control: TelegramRemoteControlConfig,
        reload_callback: ReloadCallback,
        status_callback: StatusCallback,
    ) -> None:
        """TelegramRemoteController를 초기화합니다.

        Args:
            bot_token: Telegram bot token
            remote_control: 원격제어 설정
            reload_callback: reload 명령 실행 콜백
            status_callback: status 명령 응답 콜백
        """
        self.bot_token = bot_token
        self.remote_control = remote_control
        self.reload_callback = reload_callback
        self.status_callback = status_callback
        self.application: Application[Any, Any, Any, Any, Any, Any] | None = None

    def update_remote_control(self, remote_control: TelegramRemoteControlConfig) -> None:
        """원격제어 설정을 새 설정으로 교체합니다."""
        self.remote_control = remote_control

    def is_chat_allowed(self, chat_id: int | str | None) -> bool:
        """허용된 Telegram chat id인지 확인합니다."""
        if chat_id is None:
            return False
        return self.remote_control.enabled and str(chat_id) in self.remote_control.allowed_chat_ids

    async def start(self) -> None:
        """Telegram polling 애플리케이션을 수동으로 시작합니다."""
        if self.application is not None:
            logger.debug("Telegram remote controller already started")
            return

        application = ApplicationBuilder().token(self.bot_token).build()
        application.add_handler(CommandHandler("reload", self.handle_reload))
        application.add_handler(CommandHandler("status", self.handle_status))
        application.add_handler(CommandHandler("help", self.handle_help))

        self.application = application
        initialized = False
        started = False
        try:
            await application.initialize()
            initialized = True
            await application.start()
            started = True
            if application.updater is None:
                logger.warning("Telegram remote controller updater is not available")
            else:
                await application.updater.start_polling()
        except Exception:
            try:
                if started and application.running:
                    await application.stop()
                if initialized:
                    await application.shutdown()
            finally:
                self.application = None
            raise

        logger.info("Telegram remote controller started")

    async def stop(self) -> None:
        """Telegram polling 애플리케이션을 수동으로 중지합니다."""
        if self.application is None:
            return

        application = self.application
        try:
            if application.updater is not None:
                await application.updater.stop()
            if application.running:
                await application.stop()
            await application.shutdown()
        finally:
            self.application = None
            logger.info("Telegram remote controller stopped")

    async def handle_reload(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """reload 명령을 처리합니다."""
        del context
        if not self._is_update_allowed(update):
            return
        if not self.remote_control.commands.reload:
            await self._reply(update, "reload command disabled")
            return

        result = await self.reload_callback()
        await self._reply(update, result.message)

    async def handle_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """status 명령을 처리합니다."""
        del context
        if not self._is_update_allowed(update):
            return
        if not self.remote_control.commands.status:
            await self._reply(update, "status command disabled")
            return

        await self._reply(update, self.status_callback())

    async def handle_help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """help 명령을 처리합니다."""
        del context
        if not self._is_update_allowed(update):
            return
        if not self.remote_control.commands.help:
            await self._reply(update, "help command disabled")
            return

        await self._reply(update, "Commands:\n" + "\n".join(self._enabled_commands()))

    def _is_update_allowed(self, update: Update) -> bool:
        """update의 chat id가 원격제어 허용 대상인지 확인합니다."""
        chat = update.effective_chat
        chat_id = None if chat is None else chat.id
        if self.is_chat_allowed(chat_id):
            return True

        logger.warning("Unauthorized Telegram remote command: chat_id={}", chat_id)
        return False

    async def _reply(self, update: Update, message: str) -> None:
        """Telegram 명령에 plain text로 응답합니다."""
        if update.effective_message is None:
            logger.warning("Telegram remote command has no effective message")
            return

        await update.effective_message.reply_text(message)

    def _enabled_commands(self) -> list[str]:
        """활성화된 명령 목록을 고정 순서로 반환합니다."""
        commands = self.remote_control.commands
        enabled_commands: list[str] = []
        if commands.reload:
            enabled_commands.append("/reload")
        if commands.status:
            enabled_commands.append("/status")
        if commands.help:
            enabled_commands.append("/help")
        return enabled_commands
