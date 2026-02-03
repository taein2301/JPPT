"""Integration tests for the full application."""
from pathlib import Path

import pytest
from jppt.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_full_cli_integration(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full CLI workflow with config."""
    # Set environment variables
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    # Test version
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0

    # Test help
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout


@pytest.mark.asyncio
async def test_config_logger_integration(temp_config_dir: Path) -> None:
    """Test config and logger working together."""
    from jppt.utils.config import load_config
    from jppt.utils.logger import setup_logger

    config = load_config(env="dev", config_dir=temp_config_dir)

    log_file = temp_config_dir / "test.log"
    setup_logger(
        level=config.logging.level,
        log_file=log_file,
        format_str=config.logging.format,
    )

    from loguru import logger

    logger.info("Integration test")

    assert log_file.exists()
    assert "Integration test" in log_file.read_text()
