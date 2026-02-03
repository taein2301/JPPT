"""Pytest configuration and shared fixtures."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.jppt.utils.config import Settings


@pytest.fixture
def sample_config() -> dict[str, dict[str, str | bool]]:
    """Provide sample configuration for testing."""
    return {
        "app": {"name": "test-app", "version": "0.1.0", "debug": True},
        "logging": {"level": "DEBUG", "format": "simple"},
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
    }


@pytest.fixture
def config() -> Settings:
    """Test configuration."""
    return Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "DEBUG"},
        telegram={"enabled": False},
    )


@pytest.fixture
def mock_telegram() -> MagicMock:
    """Mock Telegram notifier."""
    mock = MagicMock()
    mock.send_message = AsyncMock()
    mock.send_error = AsyncMock()
    return mock


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client."""
    mock = MagicMock()
    mock.get = AsyncMock()
    mock.post = AsyncMock()
    return mock


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory with default.yaml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    default_file = config_dir / "default.yaml"
    default_file.write_text("""
app:
  name: "test"
  version: "0.1.0"
  debug: false

logging:
  level: "INFO"
  format: "{time} | {level} | {message}"
  rotation: "00:00"
  retention: "10 days"

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
""")

    return config_dir
