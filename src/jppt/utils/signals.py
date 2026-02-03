"""Graceful shutdown handling for signals."""

import signal
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger


class GracefulShutdown:
    """
    Handle graceful shutdown on SIGTERM/SIGINT.

    Example:
        shutdown = GracefulShutdown()
        setup_signal_handlers(shutdown)

        async with shutdown:
            while not shutdown.should_exit:
                await do_work()
    """

    def __init__(self) -> None:
        """Initialize graceful shutdown handler."""
        self.should_exit = False
        self._cleanup_callbacks: list[Callable[[], Awaitable[None]]] = []

    def register_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register cleanup callback to run on shutdown.

        Args:
            callback: Async function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signal."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.should_exit = True

    async def __aenter__(self) -> "GracefulShutdown":
        """Enter context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit context manager and run cleanup."""
        if self.should_exit:
            logger.info("Running cleanup callbacks")
            for callback in self._cleanup_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")


def setup_signal_handlers(shutdown: GracefulShutdown) -> None:
    """
    Setup signal handlers for graceful shutdown.

    Args:
        shutdown: GracefulShutdown instance to handle signals
    """
    signal.signal(signal.SIGTERM, shutdown._handle_signal)
    signal.signal(signal.SIGINT, shutdown._handle_signal)
    logger.info("Signal handlers registered (SIGTERM, SIGINT)")
