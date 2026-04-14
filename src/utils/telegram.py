"""텔레그램 알림 연동.

이 모듈은 텔레그램 봇을 통해 메시지 및 오류 알림을 전송하는 기능을 제공합니다.
"""

from collections.abc import Callable
from datetime import datetime, time
from zoneinfo import ZoneInfo

from loguru import logger
from telegram import Bot
from telegram.error import TimedOut

from src.utils.config import TelegramMessageTemplateConfig, TelegramSilentTimeConfig


class TelegramNotifier:
    """텔레그램을 통해 알림을 전송합니다.

    봇 토큰과 채팅 ID를 사용하여 메시지를 전송합니다.
    알림이 비활성화되어 있거나 전송에 실패해도 애플리케이션을 중단하지 않습니다.

    사용 예시:
        notifier = TelegramNotifier(bot_token="xxx", chat_id="yyy", enabled=True)
        await notifier.send_message("안녕하세요!")
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool = True,
        silent_time: TelegramSilentTimeConfig | None = None,
        templates: TelegramMessageTemplateConfig | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        """텔레그램 알림 전송기를 초기화합니다.

        Args:
            bot_token: 텔레그램 봇 토큰
            chat_id: 텔레그램 채팅방 ID
            enabled: 알림 활성화 여부
            silent_time: 무음 시간 설정
            templates: 메시지 템플릿 설정
            now_provider: 현재 시각 주입 함수 (테스트용)
        """
        self.enabled = enabled
        self.chat_id = chat_id
        self._bot: Bot | None = None
        self._silent_time = silent_time or TelegramSilentTimeConfig()
        self._templates = templates or TelegramMessageTemplateConfig()
        self._now_provider = now_provider or self._default_now_provider

        if enabled and bot_token:
            self._bot = Bot(token=bot_token)
            logger.info(f"Telegram notifier initialized: chat_id={chat_id}")
        elif enabled:
            logger.warning("Telegram enabled but bot_token is empty")

    def _default_now_provider(self) -> datetime:
        """설정된 타임존 기준 현재 시각을 반환합니다."""
        return datetime.now(ZoneInfo(self._silent_time.timezone))

    @staticmethod
    def _parse_hhmm(value: str) -> time:
        """HH:MM 문자열을 time 객체로 변환합니다."""
        return datetime.strptime(value, "%H:%M").time()

    def _is_silent_time(self) -> bool:
        """현재 시각이 무음 시간 구간인지 확인합니다."""
        if not self._silent_time.enabled:
            return False

        now = self._now_provider().astimezone(ZoneInfo(self._silent_time.timezone)).time()
        start = self._parse_hhmm(self._silent_time.start)
        end = self._parse_hhmm(self._silent_time.end)

        if start <= end:
            return start <= now < end

        return now >= start or now < end

    @staticmethod
    def format_status_message(
        app_name: str,
        status: str,
        *,
        env: str | None = None,
        reason: str | None = None,
    ) -> str:
        """실행 상태 알림 메시지를 지정된 포맷으로 생성합니다.

        Args:
            app_name: 애플리케이션 이름
            status: 상태 문자열
            env: 실행 환경 이름
            reason: 종료/완료 사유
        """
        lines = [f"[{app_name}] {status}"]

        if env is not None:
            lines.append(f"Env : {env}")
        if reason is not None:
            lines.append(f"Reason : {reason}")

        return "\n".join(lines)

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
    ) -> bool:
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
            return False
        if self._is_silent_time():
            logger.info(
                "Telegram notification skipped due to silent time: {}-{} ({})",
                self._silent_time.start,
                self._silent_time.end,
                self._silent_time.timezone,
            )
            return False

        try:
            await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            logger.info(f"Telegram message sent to {self.chat_id}")
            return True
        except TimedOut:
            logger.warning(
                (
                    "Telegram send request timed out for chat_id={}. "
                    "Message delivery may have succeeded."
                ),
                self.chat_id,
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            # 예외를 발생시키지 않음 - 알림 실패가 앱을 중단해서는 안 됨
            return False

    async def send_template(
        self,
        template: str,
        parse_mode: str = "Markdown",
        **kwargs: str,
    ) -> bool:
        """템플릿 문자열에 값을 채워 텔레그램 메시지를 전송합니다.

        Args:
            template: Python format 문자열 템플릿
            parse_mode: 파싱 모드 (Markdown, HTML)
            **kwargs: 템플릿 치환 값
        """
        try:
            message = template.format(**kwargs)
        except KeyError as exc:
            logger.error("Telegram template rendering failed: missing key {}", exc.args[0])
            return False

        return await self.send_message(message=message, parse_mode=parse_mode)

    async def send_error(self, error: Exception, context: str = "") -> bool:
        """오류 발생 알림을 텔레그램으로 전송합니다.

        Args:
            error: 발생한 예외
            context: 오류에 대한 추가 컨텍스트 정보
        """
        context_section = f"**Context:** {context}\n\n" if context else ""
        return await self.send_template(
            template=self._templates.error_alert,
            context=context,
            context_section=context_section,
            error_type=type(error).__name__,
            error_message=str(error),
        )
