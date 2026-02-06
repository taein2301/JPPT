"""Test CLI entry point."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from src.main import app

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
    assert "데몬" in result.stdout or "장시간" in result.stdout


def test_batch_command_help() -> None:
    """Test batch command help."""
    result = runner.invoke(app, ["batch", "--help"])
    assert result.exit_code == 0
    assert "일회성" in result.stdout or "배치" in result.stdout


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_start_command_basic(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
    temp_config_dir: Path,
) -> None:
    """Test start command basic execution."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["start", "--env", "dev"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_start_command_with_verbose(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """Test start command with verbose flag."""
    from src.utils.config import Settings

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


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_batch_command_basic(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """Test batch command basic execution."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["batch", "--env", "dev"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_batch_command_with_custom_config(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
    temp_config_dir: Path,
) -> None:
    """Test batch command with custom config path."""
    from src.utils.config import Settings

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


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_log_file_path_is_in_project_root(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
) -> None:
    """Test that log file path is relative to project root, not cwd."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "INFO"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0

    # Verify setup_logger was called with absolute path to project root/logs
    call_kwargs = mock_setup_logger.call_args[1]
    log_file = call_kwargs["log_file"]

    # Log file should be: PROJECT_ROOT / "logs" / "test-app_{time:YYYYMMDD}.log"
    # PROJECT_ROOT is src/main.py의 parent.parent
    assert log_file.is_absolute(), f"Log file path should be absolute, got: {log_file}"
    assert log_file.parts[-2] == "logs", f"Log file should be in 'logs' directory, got: {log_file}"
    assert log_file.name == "test-app_{time:YYYYMMDD}.log"
