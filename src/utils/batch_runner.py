"""일회성 실행을 위한 배치 모드 실행기.

이 모듈은 작업을 한 번 실행하고 종료하는 배치 모드를 담당합니다.
"""

from loguru import logger

from src.utils.config import Settings
from src.utils.telegram import TelegramNotifier


async def run_batch(settings: Settings) -> None:
    """배치 모드를 실행합니다 (일회성 실행).

    이 함수는 템플릿 구현입니다. 실제 비즈니스 로직으로 교체하세요.

    Args:
        settings: 애플리케이션 설정

    사용 예시:
        async def run_batch(settings: Settings) -> None:
            logger.info("배치 작업 시작")

            # 실제 로직
            result = await process_data()

            logger.info(f"배치 작업 완료: {result}")
    """
    logger.info("Batch mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    # Telegram notifier 초기화
    notifier = TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        enabled=settings.telegram.enabled,
    )

    # 시작 알림 전송
    await notifier.send_message(
        f"▶️ **{settings.app.name}** batch started\nVersion: {settings.app.version}"
    )

    try:
        # TODO: 배치 로직 구현
        logger.warning("Batch runner is a template - implement your logic")

        logger.info("Batch mode completed")
        # 완료 알림
        await notifier.send_message(f"✅ **{settings.app.name}** batch completed")
    except Exception as e:
        logger.error(f"Batch failed: {e}")
        # 에러 알림
        await notifier.send_error(e, context="Batch mode failed")
        raise
