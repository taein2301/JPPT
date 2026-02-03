"""장시간 실행되는 데몬을 위한 앱 모드 실행기.

이 모듈은 시그널 처리와 graceful shutdown을 지원하는 앱 모드 실행을 담당합니다.
"""

import asyncio

from loguru import logger

from src.utils.config import Settings
from src.utils.signals import GracefulShutdown, setup_signal_handlers


async def run_app(settings: Settings) -> None:
    """앱 모드를 실행합니다 (graceful shutdown 지원 데몬).

    이 함수는 템플릿 구현입니다. 실제 비즈니스 로직으로 교체하세요.

    Args:
        settings: 애플리케이션 설정

    사용 예시:
        async def run_app(settings: Settings) -> None:
            shutdown = GracefulShutdown()
            setup_signal_handlers(shutdown)

            async def cleanup() -> None:
                logger.info("리소스 정리 중")
                await close_connections()

            shutdown.register_cleanup(cleanup)

            async with shutdown:
                while not shutdown.should_exit:
                    await process_iteration()
                    await asyncio.sleep(1)
    """
    logger.info("App mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    # Graceful shutdown 설정
    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)

    # TODO: 정리 콜백 등록
    # shutdown.register_cleanup(your_cleanup_function)

    async with shutdown:
        logger.info("App running (Press Ctrl+C to stop)")

        # TODO: 메인 루프 구현
        iteration = 0
        while not shutdown.should_exit:
            iteration += 1
            logger.debug(f"App iteration {iteration}")
            await asyncio.sleep(5)  # 실제 로직으로 교체

    logger.info("App mode stopped")
