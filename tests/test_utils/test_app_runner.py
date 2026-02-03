import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.jppt.utils.app_runner import run_app
from src.jppt.utils.config import Settings


@pytest.mark.asyncio
async def test_run_app_shutdown() -> None:
    settings = Settings()

    # Mock the shutdown to exit immediately
    with patch("src.jppt.utils.app_runner.GracefulShutdown") as mock_shutdown_class:
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True  # Exit immediately
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown

        # Should exit quickly
        await run_app(settings)
