"""시그널을 처리하는 Graceful Shutdown 구현.

이 모듈은 SIGTERM, SIGINT 시그널을 받아 정상적으로 종료하는 기능을 제공합니다.
정리(cleanup) 콜백을 등록하여 종료 시 리소스를 안전하게 해제할 수 있습니다.
"""

import signal
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger


class GracefulShutdown:
    """SIGTERM/SIGINT 시그널에 대한 graceful shutdown 처리.

    비동기 컨텍스트 매니저로 사용하며, 종료 시그널을 받으면
    등록된 정리 콜백을 순서대로 실행합니다.

    사용 예시:
        shutdown = GracefulShutdown()
        setup_signal_handlers(shutdown)

        async with shutdown:
            while not shutdown.should_exit:
                await do_work()
    """

    def __init__(self) -> None:
        """Graceful shutdown 핸들러를 초기화합니다."""
        self.should_exit = False  # 종료 플래그
        self._cleanup_callbacks: list[Callable[[], Awaitable[None]]] = []  # 정리 콜백 목록

    def register_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
        """종료 시 실행할 정리 콜백을 등록합니다.

        Args:
            callback: 정리 단계에서 호출할 비동기 함수
        """
        self._cleanup_callbacks.append(callback)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        """종료 시그널을 처리합니다."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.should_exit = True

    async def __aenter__(self) -> "GracefulShutdown":
        """컨텍스트 매니저 진입."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """컨텍스트 매니저 종료 및 정리 콜백 실행."""
        if self.should_exit:
            logger.info("Running cleanup callbacks")
            for callback in self._cleanup_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")


def setup_signal_handlers(shutdown: GracefulShutdown) -> None:
    """Graceful shutdown을 위한 시그널 핸들러를 설정합니다.

    SIGTERM과 SIGINT 시그널을 받으면 shutdown 인스턴스의 플래그를 설정합니다.

    Args:
        shutdown: 시그널을 처리할 GracefulShutdown 인스턴스
    """
    signal.signal(signal.SIGTERM, shutdown._handle_signal)
    signal.signal(signal.SIGINT, shutdown._handle_signal)
    logger.info("Signal handlers registered (SIGTERM, SIGINT)")
