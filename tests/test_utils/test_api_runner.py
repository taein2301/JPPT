"""Tests for API runner."""

from types import SimpleNamespace
from unittest.mock import patch

from src.utils.api_runner import run_api_server
from src.utils.config import Settings


@patch("src.api.app.create_api_app")
@patch("uvicorn.run")
def test_run_api_server_uses_explicit_log_level(
    mock_uvicorn_run, mock_create_api_app
) -> None:
    settings = Settings(logging={"level": "INFO"})
    mock_create_api_app.return_value = SimpleNamespace()

    run_api_server(settings, log_level="ERROR")

    assert mock_uvicorn_run.call_args.kwargs["log_level"] == "error"


@patch("src.api.app.create_api_app")
@patch("uvicorn.run")
def test_run_api_server_falls_back_to_settings_log_level(
    mock_uvicorn_run, mock_create_api_app
) -> None:
    settings = Settings(logging={"level": "WARNING"})
    mock_create_api_app.return_value = SimpleNamespace()

    run_api_server(settings)

    assert mock_uvicorn_run.call_args.kwargs["log_level"] == "warning"
