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
    assert settings.api.host == "0.0.0.0"
    assert settings.api.port == 8000
    assert settings.api.docs_enabled is True


def test_load_config_complete(tmp_path: Path) -> None:
    """Test loading complete environment config."""
    default_file = tmp_path / "default.yaml"
    default_file.write_text(
        """
app:
  name: "base"
  version: "0.0.1"
  debug: false
logging:
  level: "INFO"
  format: "base format"
  json_logs: false
  rotation: "00:00"
  retention: "10 days"
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
api:
  host: "127.0.0.1"
  port: 8100
  reload: false
  docs_enabled: true
  cors_origins:
    - "http://localhost:3000"
"""
    )

    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text(
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
api:
  port: 9100
  reload: true
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)
    assert config.app.debug is True
    assert config.logging.level == "DEBUG"
    assert config.logging.json_logs is False
    assert config.app.name == "test"
    assert config.app.version == "0.0.1"
    assert config.api.host == "127.0.0.1"
    assert config.api.port == 9100
    assert config.api.reload is True
    assert config.api.cors_origins == ["http://localhost:3000"]


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Test error when config file is missing."""
    (tmp_path / "default.yaml").write_text("app:\n  name: base\n")

    with pytest.raises(ConfigurationError, match="Config file not found"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_missing_default_file(tmp_path: Path) -> None:
    """기본 설정 파일이 없으면 예외가 발생해야 한다."""
    (tmp_path / "dev.yaml").write_text("app:\n  name: test\n")

    with pytest.raises(ConfigurationError, match="Default config file not found"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_with_telegram_silent_time(tmp_path: Path) -> None:
    """텔레그램 silent time 설정을 로드해야 한다."""
    default_file = tmp_path / "default.yaml"
    default_file.write_text(
        """
app:
  name: "base"
  version: "0.0.1"
  debug: false
logging:
  level: "INFO"
  format: "base format"
  json_logs: false
  rotation: "00:00"
  retention: "10 days"
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: true
    start: "23:00"
    end: "08:00"
    timezone: "Asia/Seoul"
api:
  host: "127.0.0.1"
  port: 8100
  reload: false
  docs_enabled: true
  cors_origins: []
"""
    )
    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text(
        """
telegram:
  silent_time:
    start: "22:30"
"""
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.silent_time.enabled is True
    assert config.telegram.silent_time.start == "22:30"
    assert config.telegram.silent_time.end == "08:00"
    assert config.telegram.silent_time.timezone == "Asia/Seoul"


def test_load_config_allows_unknown_timezone_when_silent_time_disabled(tmp_path: Path) -> None:
    """silent time이 비활성화면 타임존 검증을 건너뛰어야 한다."""
    default_file = tmp_path / "default.yaml"
    default_file.write_text(
        """
app:
  name: "base"
  version: "0.0.1"
  debug: false
logging:
  level: "INFO"
  format: "base format"
  json_logs: false
  rotation: "00:00"
  retention: "10 days"
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: false
    start: "23:00"
    end: "08:00"
    timezone: "Invalid/Timezone"
api:
  host: "127.0.0.1"
  port: 8100
  reload: false
  docs_enabled: true
  cors_origins: []
"""
    )
    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text("")

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.telegram.silent_time.enabled is False
    assert config.telegram.silent_time.timezone == "Invalid/Timezone"


def test_load_config_rejects_unknown_timezone_when_silent_time_enabled(tmp_path: Path) -> None:
    """silent time이 활성화면 유효한 타임존이어야 한다."""
    default_file = tmp_path / "default.yaml"
    default_file.write_text(
        """
app:
  name: "base"
  version: "0.0.1"
  debug: false
logging:
  level: "INFO"
  format: "base format"
  json_logs: false
  rotation: "00:00"
  retention: "10 days"
telegram:
  enabled: true
  bot_token: "token"
  chat_id: "chat"
  silent_time:
    enabled: true
    start: "23:00"
    end: "08:00"
    timezone: "Invalid/Timezone"
api:
  host: "127.0.0.1"
  port: 8100
  reload: false
  docs_enabled: true
  cors_origins: []
"""
    )
    dev_file = tmp_path / "dev.yaml"
    dev_file.write_text("")

    with pytest.raises(ValueError, match="Timezone must be a valid IANA timezone"):
        load_config(env="dev", config_dir=tmp_path)
