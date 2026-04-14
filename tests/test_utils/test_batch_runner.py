from unittest.mock import AsyncMock, patch

import pytest

from src.utils.batch_runner import run_batch
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_batch() -> None:
    settings = Settings()

    with patch(
        "src.utils.batch_runner.TelegramNotifier.send_message",
        new_callable=AsyncMock,
    ) as mock_send:
        # Should complete without error
        await run_batch(settings, "prod")

    assert mock_send.await_args_list[0].args[0] == "[jppt] 📦 batch start\nEnv : prod"
    assert mock_send.await_args_list[1].args[0] == "[jppt] ✅ batch completed\nReason : completed"
