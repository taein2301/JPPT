"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_config() -> dict[str, dict[str, str | bool]]:
    """Provide sample configuration for testing."""
    return {
        "app": {"name": "test-app", "version": "0.1.0", "debug": True},
        "logging": {"level": "DEBUG", "format": "simple"},
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
    }
