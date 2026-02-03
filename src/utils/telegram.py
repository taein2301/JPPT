"""텔레그램 알림 연동.

이 모듈은 텔레그램 봇을 통해 메시지 및 오류 알림을 전송하는 기능을 제공합니다.
"""

from loguru import logger
from telegram import Bot


class TelegramNotifier:
    """텔레그램을 통해 알림을 전송합니다.

    봇 토큰과 채팅 ID를 사용하여 메시지를 전송합니다.
    알림이 비활성화되어 있거나 전송에 실패해도 애플리케이션을 중단하지 않습니다.

    사용 예시:
        notifier = TelegramNotifier(bot_token="xxx", chat_id="yyy", enabled=True)
        await notifier.send_message("안녕하세요!")
    """

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True) -> None:
        """텔레그램 알림 전송기를 초기화합니다.

        Args:
            bot_token: 텔레그램 봇 토큰
            chat_id: 텔레그램 채팅방 ID
            enabled: 알림 활성화 여부
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
        """텔레그램으로 메시지를 전송합니다.

        Args:
            message: 전송할 메시지 텍스트
            parse_mode: 파싱 모드 (Markdown, HTML)

        참고:
            전송 실패 시에도 예외를 발생시키지 않습니다.
            알림은 애플리케이션 동작을 방해해서는 안 되기 때문입니다.
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
            # 예외를 발생시키지 않음 - 알림 실패가 앱을 중단해서는 안 됨

    async def send_error(self, error: Exception, context: str = "") -> None:
        """오류 발생 알림을 텔레그램으로 전송합니다.

        Args:
            error: 발생한 예외
            context: 오류에 대한 추가 컨텍스트 정보
        """
        message = "🚨 **Error Alert**\n\n"
        if context:
            message += f"**Context:** {context}\n\n"
        message += f"**Error:** `{type(error).__name__}`\n"
        message += f"**Message:** {str(error)}"

        await self.send_message(message)
