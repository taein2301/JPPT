"""App mode runner for long-running daemon execution."""

import asyncio

from loguru import logger

from src.jppt.utils.config import Settings
from src.jppt.utils.signals import GracefulShutdown, setup_signal_handlers


async def run_app(settings: Settings) -> None:
    """
    Run app mode (daemon with graceful shutdown).

    Args:
        settings: Application settings

    Example:
        This is a template function. Replace with your business logic:

        async def run_app(settings: Settings) -> None:
            shutdown = GracefulShutdown()
            setup_signal_handlers(shutdown)

            async def cleanup() -> None:
                logger.info("Cleaning up resources")
                await close_connections()

            shutdown.register_cleanup(cleanup)

            async with shutdown:
                while not shutdown.should_exit:
                    await process_iteration()
                    await asyncio.sleep(1)
    """
    logger.info("App mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)

    # TODO: Register cleanup callbacks
    # shutdown.register_cleanup(your_cleanup_function)

    async with shutdown:
        logger.info("App running (Press Ctrl+C to stop)")

        # TODO: Implement your main loop here
        iteration = 0
        while not shutdown.should_exit:
            iteration += 1
            logger.debug(f"App iteration {iteration}")
            await asyncio.sleep(5)  # Replace with your logic

    logger.info("App mode stopped")
