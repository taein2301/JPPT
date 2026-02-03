"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = Field(default="jppt")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )
    rotation: str = Field(default="00:00")
    retention: str = Field(default="10 days")


class TelegramConfig(BaseModel):
    """Telegram configuration."""

    enabled: bool = Field(default=False)
    bot_token: str = Field(default="")
    chat_id: str = Field(default="")


class Settings(BaseSettings):
    """Application settings loaded from YAML files."""

    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


def load_config(env: str = "dev", config_dir: Path | None = None) -> Settings:
    """
    Load configuration from YAML files.

    Args:
        env: Environment name (dev, prod)
        config_dir: Configuration directory path

    Returns:
        Settings object with loaded configuration

    Raises:
        ConfigurationError: If configuration files are missing or invalid
    """
    from jppt.utils.exceptions import ConfigurationError

    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent.parent / "config"

    default_file = config_dir / "default.yaml"
    env_file = config_dir / f"{env}.yaml"

    if not default_file.exists():
        raise ConfigurationError(f"Default config not found: {default_file}")

    # Load default config
    with open(default_file) as f:
        default_data: dict[str, Any] = yaml.safe_load(f) or {}

    # Merge with environment-specific config if exists
    if env_file.exists():
        with open(env_file) as f:
            env_data: dict[str, Any] = yaml.safe_load(f) or {}
            # Deep merge
            for key, value in env_data.items():
                if key in default_data and isinstance(default_data[key], dict):
                    default_data[key].update(value)
                else:
                    default_data[key] = value

    # Override with environment variables
    if bot_token := os.getenv("TELEGRAM_BOT_TOKEN"):
        default_data.setdefault("telegram", {})["bot_token"] = bot_token
    if chat_id := os.getenv("TELEGRAM_CHAT_ID"):
        default_data.setdefault("telegram", {})["chat_id"] = chat_id

    return Settings(**default_data)
