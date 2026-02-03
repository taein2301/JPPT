"""Tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.jppt.utils.config import Settings, load_config
from src.jppt.utils.exceptions import ConfigurationError


def test_load_config_default() -> None:
    """Test loading default configuration."""
    config = load_config(env="dev")
    assert config.app.name == "jppt"
    assert config.app.version == "0.1.0"


def test_settings_default_values() -> None:
    """Test default values in Settings."""
    settings = Settings()
    assert settings.app.debug is False
    assert settings.logging.level == "INFO"


def test_load_config_with_env_override(tmp_path: Path) -> None:
    """Test loading config with environment-specific overrides."""
    # Create test config files
    default_file = tmp_path / "default.yaml"
    default_file.write_text("""
app:
  name: "test"
  debug: false
logging:
  level: "INFO"
telegram:
  enabled: false
""")

    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text("""
app:
  debug: true
logging:
  level: "DEBUG"
""")

    config = load_config(env="dev", config_dir=tmp_path)
    assert config.app.debug is True
    assert config.logging.level == "DEBUG"
    assert config.app.name == "test"  # From default


def test_load_config_missing_default(tmp_path: Path) -> None:
    """Test error when default config is missing."""
    with pytest.raises(ConfigurationError, match="Default config not found"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_with_env_variables(tmp_path: Path) -> None:
    """Test loading config with environment variables override."""
    default_file = tmp_path / "default.yaml"
    default_file.write_text("""
app:
  name: "test"
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
""")

    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"},
    ):
        config = load_config(env="dev", config_dir=tmp_path)
        assert config.telegram.bot_token == "test-token"
        assert config.telegram.chat_id == "12345"
