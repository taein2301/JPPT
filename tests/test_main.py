"""Test CLI entry point."""

from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from src.main import CLI_NAME, app

runner = CliRunner()


def _capture_coroutine(mock_asyncio_run: AsyncMock):
    """asyncio.run에 전달된 코루틴을 반환하고 테스트 종료 시 닫도록 합니다."""
    coroutine = mock_asyncio_run.call_args.args[0]
    assert coroutine.cr_frame is not None
    return coroutine


def test_cli_version() -> None:
    """Test --version flag."""
    with (
        patch("src.main.load_config", side_effect=AssertionError("load_config should not run")),
        patch("src.main.version", return_value="9.9.9"),
    ):
        result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"{CLI_NAME} version 9.9.9"


def test_cli_version_uses_fallback_when_package_metadata_is_missing() -> None:
    """Test --version fallback without installed package metadata."""
    with (
        patch("src.main.load_config", side_effect=AssertionError("load_config should not run")),
        patch("src.main.version", side_effect=PackageNotFoundError),
    ):
        result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"{CLI_NAME} version 0.1.0"


def test_cli_help() -> None:
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout
    assert "api" not in result.stdout.lower()


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
        logging={"level": "DEBUG", "json_logs": False},
        telegram={"enabled": False},
    )

    with patch("src.main.logger.info") as mock_logger_info:
        result = runner.invoke(app, ["start", "--env", "dev"])

    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    call_kwargs = mock_setup_logger.call_args[1]
    assert call_kwargs["json_logs"] is False
    assert any(
        "Loaded config summary" in str(call.args[0]) for call in mock_logger_info.call_args_list
    )
    coroutine = _capture_coroutine(mock_asyncio_run)
    assert coroutine.cr_frame.f_locals["env"] == "dev"
    coroutine.close()


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_start_command_with_verbose(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """verbose flag should force DEBUG logging."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "INFO"},
        telegram={"enabled": False},
    )

    mock_asyncio_run.side_effect = lambda coroutine: coroutine.close()
    result = runner.invoke(app, ["start", "--verbose"])
    assert result.exit_code == 0
    # Verify DEBUG level was set due to verbose
    call_kwargs = mock_setup_logger.call_args[1]
    assert call_kwargs["level"] == "DEBUG"


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_start_command_uses_cli_log_level_override(
    mock_load_config: AsyncMock, mock_setup_logger: AsyncMock, mock_asyncio_run: AsyncMock
) -> None:
    """--log-level should override the configured logging level."""
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )

    mock_asyncio_run.side_effect = lambda coroutine: coroutine.close()
    result = runner.invoke(app, ["start", "--log-level", "ERROR"])
    assert result.exit_code == 0
    call_kwargs = mock_setup_logger.call_args[1]
    assert call_kwargs["level"] == "ERROR"


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
        logging={"level": "DEBUG", "json_logs": False},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["batch", "--env", "dev"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    coroutine = _capture_coroutine(mock_asyncio_run)
    assert coroutine.cr_frame.f_locals["env"] == "dev"
    coroutine.close()


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
        logging={"level": "DEBUG", "json_logs": False},
        telegram={"enabled": False},
    )

    custom_config = temp_config_dir / "custom.yaml"
    mock_asyncio_run.side_effect = lambda coroutine: coroutine.close()
    result = runner.invoke(app, ["batch", "--config", str(custom_config)])
    assert result.exit_code == 0
    # Verify config_dir was passed
    call_kwargs = mock_load_config.call_args[1]
    assert call_kwargs["config_dir"] == temp_config_dir


@patch("src.main.asyncio.run")
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_log_file_path_is_in_home_directory(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
) -> None:
    """Test that log file path is in user's home directory ($HOME/logs)."""
    from pathlib import Path

    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "INFO", "json_logs": False},
        telegram={"enabled": False},
    )

    mock_asyncio_run.side_effect = lambda coroutine: coroutine.close()
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0

    # Verify setup_logger was called with path to $HOME/logs
    call_kwargs = mock_setup_logger.call_args[1]
    log_file = call_kwargs["log_file"]

    # Log file should be: $HOME / "logs" / "test-app.log"
    home_logs = Path.home() / "logs"
    assert log_file.is_absolute(), f"Log file path should be absolute, got: {log_file}"
    assert log_file.parent == home_logs, f"Log file should be in $HOME/logs, got: {log_file.parent}"
    assert log_file.name == "test-app.log"
