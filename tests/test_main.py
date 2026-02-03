"""Test CLI entry point."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from jppt.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_version() -> None:
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "jppt" in result.stdout.lower()


def test_cli_help() -> None:
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout


def test_start_command_help() -> None:
    """Test start command help."""
    result = runner.invoke(app, ["start", "--help"])
    assert result.exit_code == 0
    assert "daemon" in result.stdout.lower()


def test_batch_command_help() -> None:
    """Test batch command help."""
    result = runner.invoke(app, ["batch", "--help"])
    assert result.exit_code == 0
    assert "one-shot" in result.stdout.lower()


@patch("jppt.main.asyncio.run")
@patch("jppt.main.setup_logger")
@patch("jppt.main.load_config")
def test_start_command_basic(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
    temp_config_dir: Path,
) -> None:
    """Test start command basic execution."""
    from jppt.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["start", "--env", "dev"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("jppt.main.asyncio.run")
@patch("jppt.main.setup_logger")
@patch("jppt.main.load_config")
def test_start_command_with_verbose(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """Test start command with verbose flag."""
    from jppt.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "INFO"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["start", "--verbose"])
    assert result.exit_code == 0
    # Verify DEBUG level was set due to verbose
    call_kwargs = mock_setup_logger.call_args[1]
    assert call_kwargs["level"] == "DEBUG"


@patch("jppt.main.asyncio.run")
@patch("jppt.main.setup_logger")
@patch("jppt.main.load_config")
def test_batch_command_basic(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """Test batch command basic execution."""
    from jppt.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["batch", "--env", "dev"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("jppt.main.asyncio.run")
@patch("jppt.main.setup_logger")
@patch("jppt.main.load_config")
def test_batch_command_with_custom_config(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
    temp_config_dir: Path,
) -> None:
    """Test batch command with custom config path."""
    from jppt.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    custom_config = temp_config_dir / "custom.yaml"
    result = runner.invoke(app, ["batch", "--config", str(custom_config)])
    assert result.exit_code == 0
    # Verify config_dir was passed
    call_kwargs = mock_load_config.call_args[1]
    assert call_kwargs["config_dir"] == temp_config_dir
