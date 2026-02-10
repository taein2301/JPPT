"""Tests for configuration management."""

import tomllib
from pathlib import Path

import pytest

from src.utils.config import Settings, load_config
from src.utils.exceptions import ConfigurationError


def test_load_config_default() -> None:
    """Test loading default configuration."""
    config = load_config(env="dev")

    # Read actual project name from pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    expected_name = pyproject["project"]["name"]

    assert config.app.name == expected_name
    assert config.app.version == "0.1.0"


def test_settings_default_values() -> None:
    """Test default values in Settings."""
    settings = Settings()
    assert settings.app.debug is False
    assert settings.logging.level == "INFO"


def test_load_config_complete(tmp_path: Path) -> None:
    """Test loading complete environment config."""
    # Create test config file
    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text(
        """
app:
  name: "test"
  version: "0.1.0"
  debug: true
logging:
  level: "DEBUG"
  format: "test format"
  rotation: "00:00"
  retention: "10 days"
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)
    assert config.app.debug is True
    assert config.logging.level == "DEBUG"
    assert config.app.name == "test"


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Test error when config file is missing."""
    with pytest.raises(ConfigurationError, match="Config file not found"):
        load_config(env="dev", config_dir=tmp_path)
