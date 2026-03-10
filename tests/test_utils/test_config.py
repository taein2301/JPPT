"""Tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from src.utils.config import Settings, load_config
from src.utils.exceptions import ConfigurationError


def test_load_config_default() -> None:
    """Test loading default configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "dev.yaml.example"
    config_dir = config_path.parent
    temp_config = config_dir / "dev.yaml"
    temp_config.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    expected = yaml.safe_load(config_path.read_text(encoding="utf-8"))["app"]

    try:
        config = load_config(env="dev")
    finally:
        temp_config.unlink(missing_ok=True)

    assert config.app.name == expected["name"]
    assert config.app.version == expected["version"]


def test_settings_default_values() -> None:
    """Test default values in Settings."""
    settings = Settings()
    assert settings.app.debug is False
    assert settings.logging.level == "INFO"
    assert settings.logging.json_logs is False


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
  json_logs: false
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
    assert config.logging.json_logs is False
    assert config.app.name == "test"


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Test error when config file is missing."""
    with pytest.raises(ConfigurationError, match="Config file not found"):
        load_config(env="dev", config_dir=tmp_path)
