import asyncio
import signal
from unittest.mock import AsyncMock, patch

import pytest

from src.jppt.utils.signals import GracefulShutdown, setup_signal_handlers


@pytest.mark.asyncio
async def test_graceful_shutdown_context() -> None:
    shutdown = GracefulShutdown()

    assert shutdown.should_exit is False

    async with shutdown:
        assert shutdown.should_exit is False

    # After exit, should still be False (no signal received)
    assert shutdown.should_exit is False


@pytest.mark.asyncio
async def test_graceful_shutdown_signal_handling() -> None:
    shutdown = GracefulShutdown()
    cleanup_called = False

    async def cleanup() -> None:
        nonlocal cleanup_called
        cleanup_called = True

    shutdown.register_cleanup(cleanup)

    # Simulate signal
    shutdown._handle_signal(signal.SIGTERM, None)

    assert shutdown.should_exit is True

    # Run cleanup
    async with shutdown:
        pass

    assert cleanup_called is True


def test_setup_signal_handlers() -> None:
    shutdown = GracefulShutdown()

    with patch("signal.signal") as mock_signal:
        setup_signal_handlers(shutdown)

        # Should register SIGTERM and SIGINT
        assert mock_signal.call_count == 2
