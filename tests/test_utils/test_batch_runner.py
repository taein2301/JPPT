import pytest
from jppt.utils.batch_runner import run_batch
from jppt.utils.config import Settings


@pytest.mark.asyncio
async def test_run_batch() -> None:
    settings = Settings()

    # Should complete without error
    await run_batch(settings)
