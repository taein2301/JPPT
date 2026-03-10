"""Integration tests for the full application."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def test_full_cli_integration(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full CLI workflow with config."""
    _ = (temp_config_dir, monkeypatch)

    from src.utils.config import Settings

    with patch("main.load_config") as mock_load_config:
        mock_load_config.return_value = Settings(
            app={"name": "test-app", "version": "0.1.0", "debug": False}
        )
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
    from src.utils.config import load_config
    from src.utils.logger import setup_logger

    config = load_config(env="dev", config_dir=temp_config_dir)

    log_file = temp_config_dir / "test.log"
    setup_logger(
        level=config.logging.level,
        log_file=log_file,
        format_str=config.logging.format,
        json_logs=config.logging.json_logs,
    )

    from loguru import logger

    logger.info("Integration test")

    assert log_file.exists()
    assert "Integration test" in log_file.read_text()
