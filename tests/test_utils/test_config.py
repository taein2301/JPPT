"""Tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from src.utils.config import Settings, load_config
from src.utils.exceptions import ConfigurationError


def test_load_config_default(tmp_path: Path) -> None:
    """Test loading default configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "dev.yaml.example"
    config_dir = tmp_path
    temp_config = config_dir / "dev.yaml"
    temp_config.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    expected = yaml.safe_load(config_path.read_text(encoding="utf-8"))["app"]

    config = load_config(env="dev", config_dir=config_dir)

    assert config.app.name == expected["name"]
    assert config.app.version == expected["version"]


def test_settings_default_values() -> None:
    """Test default values in Settings."""
    settings = Settings()
    assert settings.app.debug is False
    assert settings.logging.level == "INFO"
    assert settings.logging.json_logs is False
    assert not hasattr(settings, "api")


def test_load_config_complete(tmp_path: Path) -> None:
    """Test loading complete environment config."""
    (tmp_path / "dev.yaml").write_text(
        """
app:
  name: "test"
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
    assert config.app.version == "0.1.0"
    assert not hasattr(config, "api")


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Test error when config file is missing."""
    with pytest.raises(ConfigurationError, match="Config file not found"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_rejects_non_mapping_root(tmp_path: Path) -> None:
    """YAML 루트가 mapping이 아니면 ConfigurationError를 발생시켜야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
- just
- a
- list
"""
    )

    with pytest.raises(ConfigurationError, match="Config file root must be a mapping"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_with_telegram_silent_time(tmp_path: Path) -> None:
    """텔레그램 silent time 설정을 로드해야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: true
    start: "22:30"
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.silent_time.enabled is True
    assert config.telegram.silent_time.start == "22:30"
    assert config.telegram.silent_time.end == "08:00"
    assert config.telegram.silent_time.timezone == "Asia/Seoul"


def test_load_config_with_telegram_templates(tmp_path: Path) -> None:
    """텔레그램 템플릿 설정을 로드해야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  templates:
    error_alert: "오류={error_type}, 메시지={error_message}"
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.templates.error_alert == "오류={error_type}, 메시지={error_message}"


def test_load_config_allows_unknown_timezone_when_silent_time_disabled(tmp_path: Path) -> None:
    """silent time이 비활성화면 타임존 검증을 건너뛰어야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: false
    start: "23:00"
    end: "08:00"
    timezone: "Invalid/Timezone"
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.silent_time.enabled is False
    assert config.telegram.silent_time.timezone == "Invalid/Timezone"


def test_load_config_rejects_unknown_timezone_when_silent_time_enabled(tmp_path: Path) -> None:
    """silent time이 활성화면 유효한 타임존이어야 한다."""
    (tmp_path / "dev.yaml").write_text(
        """
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: true
    start: "23:00"
    end: "08:00"
    timezone: "Invalid/Timezone"
"""
    )

    with pytest.raises(ValueError, match="Timezone must be a valid IANA timezone"):
        load_config(env="dev", config_dir=tmp_path)
