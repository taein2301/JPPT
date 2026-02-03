import pytest
from src.utils.batch_runner import run_batch
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_batch() -> None:
    settings = Settings()

    # Should complete without error
    await run_batch(settings)
