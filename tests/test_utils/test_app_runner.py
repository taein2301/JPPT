from unittest.mock import AsyncMock, patch

import pytest

from src.utils.app_runner import run_app
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_app_shutdown() -> None:
    settings = Settings()

    # Mock the shutdown to exit immediately
    with (
        patch("src.utils.app_runner.GracefulShutdown") as mock_shutdown_class,
        patch(
            "src.utils.app_runner.TelegramNotifier.send_message",
            new_callable=AsyncMock,
        ) as mock_send,
    ):
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True  # Exit immediately
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown

        # Should exit quickly
        await run_app(settings, "prod")

    assert mock_send.await_args_list[0].args[0] == "[jppt] start\nEnv : prod"
    assert mock_send.await_args_list[1].args[0] == "[jppt] stop\nReason : gracefully"
