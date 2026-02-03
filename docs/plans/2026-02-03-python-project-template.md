# Python Project Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a modern Python CLI application template with Typer, Pydantic settings, Loguru logging, and Telegram notifications

**Architecture:** Template follows TDD with utils-first approach. Core business logic stays in `core/`, reusable utilities in `utils/`. CLI entry point (`main.py`) delegates to mode runners (`app_runner`, `batch_runner`). Configuration uses layered YAML files (default → env-specific) with Pydantic validation.

**Tech Stack:** uv, Python 3.11+, Typer, Pydantic Settings, Loguru, httpx, tenacity, python-telegram-bot, pytest, mypy, ruff

---

## Task 1: Project Initialization

**Files:**
- Create: `pyproject.toml`
- Create: `ruff.toml`
- Create: `.gitignore`
- Create: `.gitattributes`
- Create: `README.md`

**Step 1: Initialize uv project**

Run:
```bash
uv init --name jppt --python 3.11
```

Expected: Creates basic project structure with pyproject.toml

**Step 2: Write pyproject.toml**

Create complete `pyproject.toml`:

```toml
[project]
name = "jppt"
version = "0.1.0"
description = "JKLEE Python Project Template"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.9.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "loguru>=0.7.0",
    "httpx>=0.27.0",
    "tenacity>=8.0",
    "python-telegram-bot>=21.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8",
    "ruff>=0.1.0",
    "pre-commit>=3.6.0",
    "types-pyyaml>=6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
    "--strict-markers",
    "-v"
]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "telegram.*"
ignore_missing_imports = true

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Step 3: Write ruff.toml**

Create `ruff.toml`:

```toml
[lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = []

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"

line-length = 100
target-version = "py311"
```

**Step 4: Write .gitignore**

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
config/dev.yaml
config/prod.yaml
logs/
*.log

# uv
.python-version
```

**Step 5: Write .gitattributes**

Create `.gitattributes`:

```gitattributes
# Merge strategy for app-specific files
src/core/** merge=ours
src/utils/app_runner.py merge=ours
src/utils/batch_runner.py merge=ours
config/*.yaml merge=ours
README.md merge=ours
```

**Step 6: Write README.md**

Create `README.md`:

```markdown
# JPPT - JKLEE Python Project Template

Modern Python CLI application template with best practices built-in.

## Features

- 🎯 **Typer CLI**: Clean command-line interface
- ⚙️ **Pydantic Settings**: Type-safe configuration
- 📝 **Loguru**: Structured logging with rotation
- 🔄 **Tenacity**: Retry logic for resilient operations
- 📱 **Telegram**: Built-in notifications
- 🧪 **pytest**: 80% coverage requirement
- 🔍 **mypy**: Strict type checking
- ✨ **ruff**: Fast linting and formatting

## Quick Start

\`\`\`bash
# Install dependencies
uv sync --all-extras

# Run in app mode (daemon)
uv run python -m src.main start

# Run in batch mode (one-shot)
uv run python -m src.main batch

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Type check
uv run mypy src/
\`\`\`

## Project Structure

\`\`\`
src/
├── main.py              # CLI entry point
├── core/                # Business logic
└── utils/               # Reusable utilities
    ├── config.py
    ├── logger.py
    ├── app_runner.py
    ├── batch_runner.py
    └── ...

tests/                   # Test suite
config/                  # Configuration files
docs/                    # Documentation
\`\`\`

## Configuration

1. Copy example config:
   \`\`\`bash
   cp config/dev.yaml.example config/dev.yaml
   \`\`\`

2. Edit `config/dev.yaml` with your settings

3. Set environment variables for secrets:
   \`\`\`bash
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   \`\`\`

## Development

\`\`\`bash
# Install pre-commit hooks
uv run pre-commit install

# Run all checks
uv run pre-commit run --all-files
\`\`\`

## License

MIT
```

**Step 7: Install dependencies**

Run:
```bash
uv sync --all-extras
```

Expected: All dependencies installed

**Step 8: Commit**

```bash
git add pyproject.toml ruff.toml .gitignore .gitattributes README.md
git commit -m "chore: initialize project with uv and tooling config"
```

---

## Task 2: Exception Hierarchy

**Files:**
- Create: `src/__init__.py`
- Create: `src/utils/__init__.py`
- Create: `src/utils/exceptions.py`
- Create: `tests/__init__.py`
- Create: `tests/test_utils/__init__.py`
- Create: `tests/test_utils/test_exceptions.py`

**Step 1: Write failing test for base exception**

Create `tests/test_utils/test_exceptions.py`:

```python
from src.utils.exceptions import AppException


def test_app_exception_with_message() -> None:
    exc = AppException("test error")
    assert str(exc) == "test error"
    assert exc.args == ("test error",)
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_exceptions.py::test_app_exception_with_message -v
```

Expected: FAIL with "cannot import name 'AppException'"

**Step 3: Write minimal implementation**

Create `src/utils/exceptions.py`:

```python
"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for all application errors."""

    pass
```

**Step 4: Create __init__.py files**

Create empty `src/__init__.py`, `src/utils/__init__.py`, `tests/__init__.py`, `tests/test_utils/__init__.py`

**Step 5: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_utils/test_exceptions.py::test_app_exception_with_message -v
```

Expected: PASS

**Step 6: Write tests for exception hierarchy**

Add to `tests/test_utils/test_exceptions.py`:

```python
from src.utils.exceptions import (
    AppException,
    ConfigurationError,
    HttpClientError,
    RetryExhaustedError,
    ServiceError,
    TelegramError,
    ValidationError,
)


def test_exception_hierarchy() -> None:
    """Test that all exceptions inherit from AppException."""
    assert issubclass(ConfigurationError, AppException)
    assert issubclass(ServiceError, AppException)
    assert issubclass(TelegramError, ServiceError)
    assert issubclass(HttpClientError, ServiceError)
    assert issubclass(ValidationError, AppException)
    assert issubclass(RetryExhaustedError, AppException)


def test_configuration_error() -> None:
    exc = ConfigurationError("config missing")
    assert str(exc) == "config missing"
    assert isinstance(exc, AppException)


def test_service_error() -> None:
    exc = ServiceError("service down")
    assert str(exc) == "service down"
    assert isinstance(exc, AppException)


def test_telegram_error() -> None:
    exc = TelegramError("telegram api error")
    assert str(exc) == "telegram api error"
    assert isinstance(exc, ServiceError)


def test_http_client_error() -> None:
    exc = HttpClientError("http request failed")
    assert str(exc) == "http request failed"
    assert isinstance(exc, ServiceError)
```

**Step 7: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/test_utils/test_exceptions.py -v
```

Expected: FAIL with import errors

**Step 8: Implement exception hierarchy**

Update `src/utils/exceptions.py`:

```python
"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(AppException):
    """Exception raised for configuration-related errors."""

    pass


class ServiceError(AppException):
    """Exception raised for external service errors."""

    pass


class TelegramError(ServiceError):
    """Exception raised for Telegram API errors."""

    pass


class HttpClientError(ServiceError):
    """Exception raised for HTTP client errors."""

    pass


class ValidationError(AppException):
    """Exception raised for data validation errors."""

    pass


class RetryExhaustedError(AppException):
    """Exception raised when retry attempts are exhausted."""

    pass
```

**Step 9: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_exceptions.py -v
```

Expected: All tests PASS

**Step 10: Commit**

```bash
git add src/ tests/
git commit -m "feat: add custom exception hierarchy"
```

---

## Task 3: Configuration Management

**Files:**
- Create: `src/utils/config.py`
- Create: `config/default.yaml`
- Create: `config/dev.yaml.example`
- Create: `tests/conftest.py`
- Create: `tests/test_utils/test_config.py`

**Step 1: Write failing test for config loading**

Create `tests/test_utils/test_config.py`:

```python
from pathlib import Path

from src.utils.config import Settings, load_config


def test_load_config_default() -> None:
    config = load_config(env="dev")
    assert config.app.name == "jppt"
    assert config.app.version == "0.1.0"


def test_settings_default_values() -> None:
    settings = Settings()
    assert settings.app.debug is False
    assert settings.logging.level == "INFO"
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_config.py -v
```

Expected: FAIL with import errors

**Step 3: Create default configuration**

Create `config/default.yaml`:

```yaml
app:
  name: "jppt"
  version: "0.1.0"
  debug: false

logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
  rotation: "00:00"
  retention: "10 days"

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
```

**Step 4: Create dev example**

Create `config/dev.yaml.example`:

```yaml
app:
  debug: true

logging:
  level: "DEBUG"

telegram:
  enabled: false
```

**Step 5: Implement config loader**

Create `src/utils/config.py`:

```python
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
    from src.utils.exceptions import ConfigurationError

    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"

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
```

**Step 6: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_config.py -v
```

Expected: All tests PASS

**Step 7: Add more comprehensive tests**

Add to `tests/test_utils/test_config.py`:

```python
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import Settings, load_config
from src.utils.exceptions import ConfigurationError


def test_load_config_with_env_override(tmp_path: Path) -> None:
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
    with pytest.raises(ConfigurationError, match="Default config not found"):
        load_config(env="dev", config_dir=tmp_path)


def test_load_config_with_env_variables(tmp_path: Path) -> None:
    default_file = tmp_path / "default.yaml"
    default_file.write_text("""
app:
  name: "test"
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
""")

    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"}):
        config = load_config(env="dev", config_dir=tmp_path)
        assert config.telegram.bot_token == "test-token"
        assert config.telegram.chat_id == "12345"
```

**Step 8: Run full test suite**

Run:
```bash
uv run pytest tests/test_utils/test_config.py -v
```

Expected: All tests PASS

**Step 9: Commit**

```bash
git add src/utils/config.py config/ tests/
git commit -m "feat: add pydantic-based configuration management"
```

---

## Task 4: Logging Setup

**Files:**
- Create: `src/utils/logger.py`
- Create: `tests/test_utils/test_logger.py`

**Step 1: Write failing test for logger setup**

Create `tests/test_utils/test_logger.py`:

```python
from pathlib import Path

from loguru import logger

from src.utils.logger import setup_logger


def test_setup_logger_console_only(tmp_path: Path) -> None:
    logger.remove()  # Clear existing handlers

    setup_logger(
        level="DEBUG",
        log_file=None,
        format_str="{level} | {message}"
    )

    # Logger should be configured
    assert len(logger._core.handlers) > 0


def test_setup_logger_with_file(tmp_path: Path) -> None:
    logger.remove()

    log_file = tmp_path / "test.log"
    setup_logger(
        level="INFO",
        log_file=log_file,
        format_str="{level} | {message}",
        rotation="1 MB",
        retention="1 day"
    )

    # Log a message
    logger.info("test message")

    # File should be created
    assert log_file.exists()
    assert "test message" in log_file.read_text()
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_logger.py -v
```

Expected: FAIL with import error

**Step 3: Implement logger setup**

Create `src/utils/logger.py`:

```python
"""Logging configuration using Loguru."""
import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: Path | None = None,
    format_str: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation: str = "00:00",
    retention: str = "10 days",
) -> None:
    """
    Configure Loguru logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_str: Log format string
        rotation: When to rotate log file (time or size)
        retention: How long to keep old logs
    """
    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stderr,
        format=format_str,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=format_str,
            level=level,
            rotation=rotation,
            retention=retention,
            compression=None,
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logger initialized: level={level}, file={log_file}")
```

**Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_logger.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/utils/logger.py tests/test_utils/test_logger.py
git commit -m "feat: add loguru logger configuration"
```

---

## Task 5: Retry Decorator

**Files:**
- Create: `src/utils/retry.py`
- Create: `tests/test_utils/test_retry.py`

**Step 1: Write failing test for retry decorator**

Create `tests/test_utils/test_retry.py`:

```python
import pytest

from src.utils.exceptions import RetryExhaustedError
from src.utils.retry import with_retry


def test_retry_succeeds_on_first_attempt() -> None:
    call_count = 0

    @with_retry(max_attempts=3, wait_seconds=0.01)
    def succeeds_immediately() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = succeeds_immediately()
    assert result == "success"
    assert call_count == 1


def test_retry_succeeds_after_failures() -> None:
    call_count = 0

    @with_retry(max_attempts=3, wait_seconds=0.01)
    def fails_twice() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("temporary error")
        return "success"

    result = fails_twice()
    assert result == "success"
    assert call_count == 3


def test_retry_exhausted() -> None:
    @with_retry(max_attempts=2, wait_seconds=0.01)
    def always_fails() -> str:
        raise ValueError("permanent error")

    with pytest.raises(RetryExhaustedError) as exc_info:
        always_fails()

    assert "permanent error" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_retry.py -v
```

Expected: FAIL with import error

**Step 3: Implement retry decorator**

Create `src/utils/retry.py`:

```python
"""Retry decorator using tenacity."""
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from loguru import logger
from tenacity import (
    RetryError,
    Retrying,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.exceptions import RetryExhaustedError

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    max_wait_seconds: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_seconds: Initial wait time between retries
        max_wait_seconds: Maximum wait time between retries

    Returns:
        Decorated function that retries on failure

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=wait_seconds,
                        max=max_wait_seconds,
                    ),
                    reraise=True,
                ):
                    with attempt:
                        return func(*args, **kwargs)
            except RetryError as e:
                logger.error(
                    f"Retry exhausted for {func.__name__} after {max_attempts} attempts: {e}"
                )
                raise RetryExhaustedError(
                    f"Failed after {max_attempts} attempts: {e}"
                ) from e

            # This should never be reached due to reraise=True
            raise RuntimeError("Unexpected retry behavior")

        return wrapper

    return decorator
```

**Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_retry.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/utils/retry.py tests/test_utils/test_retry.py
git commit -m "feat: add retry decorator with tenacity"
```

---

## Task 6: HTTP Client

**Files:**
- Create: `src/utils/http_client.py`
- Create: `tests/test_utils/test_http_client.py`

**Step 1: Write failing test for HTTP client**

Create `tests/test_utils/test_http_client.py`:

```python
import pytest
from httpx import Response

from src.utils.http_client import HttpClient


@pytest.mark.asyncio
async def test_http_client_get() -> None:
    async with HttpClient(base_url="https://httpbin.org") as client:
        response = await client.get("/get")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data


@pytest.mark.asyncio
async def test_http_client_timeout() -> None:
    async with HttpClient(timeout=0.001) as client:
        with pytest.raises(Exception):  # Timeout or connection error
            await client.get("https://httpbin.org/delay/10")
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_http_client.py -v
```

Expected: FAIL with import error

**Step 3: Implement HTTP client**

Create `src/utils/http_client.py`:

```python
"""HTTP client wrapper using httpx."""
from typing import Any

import httpx
from loguru import logger

from src.utils.exceptions import HttpClientError


class HttpClient:
    """
    Async HTTP client with timeout and retry support.

    Example:
        async with HttpClient(base_url="https://api.example.com") as client:
            response = await client.get("/endpoint")
            data = response.json()
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
    ) -> None:
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Total timeout for requests in seconds
            connect_timeout: Connection timeout in seconds
        """
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(timeout=timeout, connect=connect_timeout)

    async def __aenter__(self) -> "HttpClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Send GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            HttpClientError: If request fails
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.debug(f"GET {url} params={params}")
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP GET failed: {url} - {e}")
            raise HttpClientError(f"HTTP GET failed: {e}") from e

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Send POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            HttpClientError: If request fails
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.debug(f"POST {url}")
            response = await self._client.post(url, json=json, data=data, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP POST failed: {url} - {e}")
            raise HttpClientError(f"HTTP POST failed: {e}") from e
```

**Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_http_client.py -v
```

Expected: All tests PASS (may be slow due to network requests)

**Step 5: Commit**

```bash
git add src/utils/http_client.py tests/test_utils/test_http_client.py
git commit -m "feat: add async HTTP client with httpx"
```

---

## Task 7: Telegram Integration

**Files:**
- Create: `src/utils/telegram.py`
- Create: `tests/test_utils/test_telegram.py`

**Step 1: Write test with mocking for Telegram**

Create `tests/test_utils/test_telegram.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.telegram import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_send_message() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)
        await notifier.send_message("test message")

        mock_bot.send_message.assert_called_once_with(
            chat_id="12345",
            text="test message",
            parse_mode="Markdown"
        )


@pytest.mark.asyncio
async def test_telegram_disabled() -> None:
    notifier = TelegramNotifier(bot_token="", chat_id="", enabled=False)
    # Should not raise error
    await notifier.send_message("test")


@pytest.mark.asyncio
async def test_telegram_error_handling() -> None:
    with patch("src.utils.telegram.Bot") as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception("API error")
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier(bot_token="test-token", chat_id="12345", enabled=True)

        # Should not raise, just log error
        await notifier.send_message("test")
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_telegram.py -v
```

Expected: FAIL with import error

**Step 3: Implement Telegram notifier**

Create `src/utils/telegram.py`:

```python
"""Telegram notification integration."""
from loguru import logger
from telegram import Bot
from telegram.error import TelegramError

from src.utils.exceptions import TelegramError as TelegramException


class TelegramNotifier:
    """
    Send notifications via Telegram.

    Example:
        notifier = TelegramNotifier(bot_token="xxx", chat_id="yyy", enabled=True)
        await notifier.send_message("Hello!")
    """

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True) -> None:
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled
        self.chat_id = chat_id
        self._bot: Bot | None = None

        if enabled and bot_token:
            self._bot = Bot(token=bot_token)
            logger.info(f"Telegram notifier initialized: chat_id={chat_id}")
        elif enabled:
            logger.warning("Telegram enabled but bot_token is empty")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
    ) -> None:
        """
        Send message to Telegram.

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown, HTML)

        Raises:
            TelegramException: If sending fails (only when enabled)
        """
        if not self.enabled or not self._bot:
            logger.debug("Telegram notification skipped (disabled)")
            return

        try:
            await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            logger.info(f"Telegram message sent to {self.chat_id}")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            # Don't raise, just log - notifications shouldn't break the app

    async def send_error(self, error: Exception, context: str = "") -> None:
        """
        Send error notification to Telegram.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        message = f"🚨 **Error Alert**\n\n"
        if context:
            message += f"**Context:** {context}\n\n"
        message += f"**Error:** `{type(error).__name__}`\n"
        message += f"**Message:** {str(error)}"

        await self.send_message(message)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_telegram.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/utils/telegram.py tests/test_utils/test_telegram.py
git commit -m "feat: add telegram notification integration"
```

---

## Task 8: Graceful Shutdown

**Files:**
- Create: `src/utils/signals.py`
- Create: `tests/test_utils/test_signals.py`

**Step 1: Write test for signal handler**

Create `tests/test_utils/test_signals.py`:

```python
import asyncio
import signal
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.signals import GracefulShutdown, setup_signal_handlers


@pytest.mark.asyncio
async def test_graceful_shutdown_context() -> None:
    shutdown = GracefulShutdown()

    assert shutdown.should_exit is False

    async with shutdown:
        assert shutdown.should_exit is False

    # After exit, should still be False (no signal received)
    assert shutdown.should_exit is False


@pytest.mark.asyncio
async def test_graceful_shutdown_signal_handling() -> None:
    shutdown = GracefulShutdown()
    cleanup_called = False

    async def cleanup() -> None:
        nonlocal cleanup_called
        cleanup_called = True

    shutdown.register_cleanup(cleanup)

    # Simulate signal
    shutdown._handle_signal(signal.SIGTERM, None)

    assert shutdown.should_exit is True

    # Run cleanup
    async with shutdown:
        pass

    assert cleanup_called is True


def test_setup_signal_handlers() -> None:
    shutdown = GracefulShutdown()

    with patch("signal.signal") as mock_signal:
        setup_signal_handlers(shutdown)

        # Should register SIGTERM and SIGINT
        assert mock_signal.call_count == 2
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_signals.py -v
```

Expected: FAIL with import error

**Step 3: Implement signal handlers**

Create `src/utils/signals.py`:

```python
"""Graceful shutdown handling for signals."""
import asyncio
import signal
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger


class GracefulShutdown:
    """
    Handle graceful shutdown on SIGTERM/SIGINT.

    Example:
        shutdown = GracefulShutdown()
        setup_signal_handlers(shutdown)

        async with shutdown:
            while not shutdown.should_exit:
                await do_work()
    """

    def __init__(self) -> None:
        """Initialize graceful shutdown handler."""
        self.should_exit = False
        self._cleanup_callbacks: list[Callable[[], Awaitable[None]]] = []

    def register_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register cleanup callback to run on shutdown.

        Args:
            callback: Async function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signal."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.should_exit = True

    async def __aenter__(self) -> "GracefulShutdown":
        """Enter context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit context manager and run cleanup."""
        if self.should_exit:
            logger.info("Running cleanup callbacks")
            for callback in self._cleanup_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")


def setup_signal_handlers(shutdown: GracefulShutdown) -> None:
    """
    Setup signal handlers for graceful shutdown.

    Args:
        shutdown: GracefulShutdown instance to handle signals
    """
    signal.signal(signal.SIGTERM, shutdown._handle_signal)
    signal.signal(signal.SIGINT, shutdown._handle_signal)
    logger.info("Signal handlers registered (SIGTERM, SIGINT)")
```

**Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_signals.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/utils/signals.py tests/test_utils/test_signals.py
git commit -m "feat: add graceful shutdown signal handling"
```

---

## Task 9: App & Batch Runners

**Files:**
- Create: `src/utils/app_runner.py`
- Create: `src/utils/batch_runner.py`
- Create: `tests/test_utils/test_app_runner.py`
- Create: `tests/test_utils/test_batch_runner.py`

**Step 1: Write test for batch runner**

Create `tests/test_utils/test_batch_runner.py`:

```python
import pytest

from src.utils.batch_runner import run_batch
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_batch() -> None:
    settings = Settings()

    # Should complete without error
    await run_batch(settings)
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_batch_runner.py -v
```

Expected: FAIL with import error

**Step 3: Implement batch runner**

Create `src/utils/batch_runner.py`:

```python
"""Batch mode runner for one-shot execution."""
from loguru import logger

from src.utils.config import Settings


async def run_batch(settings: Settings) -> None:
    """
    Run batch mode (one-shot execution).

    Args:
        settings: Application settings

    Example:
        This is a template function. Replace with your business logic:

        async def run_batch(settings: Settings) -> None:
            logger.info("Starting batch job")

            # Your logic here
            result = await process_data()

            logger.info(f"Batch job complete: {result}")
    """
    logger.info("Batch mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    # TODO: Implement your batch logic here
    logger.warning("Batch runner is a template - implement your logic")

    logger.info("Batch mode completed")
```

**Step 4: Write test for app runner**

Create `tests/test_utils/test_app_runner.py`:

```python
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.app_runner import run_app
from src.utils.config import Settings


@pytest.mark.asyncio
async def test_run_app_shutdown() -> None:
    settings = Settings()

    # Mock the shutdown to exit immediately
    with patch("src.utils.app_runner.GracefulShutdown") as mock_shutdown_class:
        mock_shutdown = AsyncMock()
        mock_shutdown.should_exit = True  # Exit immediately
        mock_shutdown.__aenter__.return_value = mock_shutdown
        mock_shutdown.__aexit__.return_value = None
        mock_shutdown_class.return_value = mock_shutdown

        # Should exit quickly
        await run_app(settings)
```

**Step 5: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_utils/test_app_runner.py -v
```

Expected: FAIL with import error

**Step 6: Implement app runner**

Create `src/utils/app_runner.py`:

```python
"""App mode runner for long-running daemon execution."""
import asyncio

from loguru import logger

from src.utils.config import Settings
from src.utils.signals import GracefulShutdown, setup_signal_handlers


async def run_app(settings: Settings) -> None:
    """
    Run app mode (daemon with graceful shutdown).

    Args:
        settings: Application settings

    Example:
        This is a template function. Replace with your business logic:

        async def run_app(settings: Settings) -> None:
            shutdown = GracefulShutdown()
            setup_signal_handlers(shutdown)

            async def cleanup() -> None:
                logger.info("Cleaning up resources")
                await close_connections()

            shutdown.register_cleanup(cleanup)

            async with shutdown:
                while not shutdown.should_exit:
                    await process_iteration()
                    await asyncio.sleep(1)
    """
    logger.info("App mode started")
    logger.info(f"App: {settings.app.name} v{settings.app.version}")

    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)

    # TODO: Register cleanup callbacks
    # shutdown.register_cleanup(your_cleanup_function)

    async with shutdown:
        logger.info("App running (Press Ctrl+C to stop)")

        # TODO: Implement your main loop here
        iteration = 0
        while not shutdown.should_exit:
            iteration += 1
            logger.debug(f"App iteration {iteration}")
            await asyncio.sleep(5)  # Replace with your logic

    logger.info("App mode stopped")
```

**Step 7: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_utils/test_app_runner.py tests/test_utils/test_batch_runner.py -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/utils/app_runner.py src/utils/batch_runner.py tests/
git commit -m "feat: add app and batch mode runners"
```

---

## Task 10: CLI Entry Point

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/main.py`
- Create: `tests/test_core/__init__.py`
- Create: `tests/test_main.py`

**Step 1: Write test for CLI**

Create `tests/test_main.py`:

```python
from typer.testing import CliRunner

from src.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "jppt" in result.stdout.lower()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_main.py -v
```

Expected: FAIL with import error

**Step 3: Create __init__.py files**

Create empty `src/core/__init__.py` and `tests/test_core/__init__.py`

**Step 4: Implement CLI entry point**

Create `src/main.py`:

```python
"""CLI entry point using Typer."""
import asyncio
from pathlib import Path

import typer
from loguru import logger

from src.utils.config import load_config
from src.utils.logger import setup_logger

app = typer.Typer(
    name="jppt",
    help="JKLEE Python Project Template",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo("jppt version 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """JKLEE Python Project Template - Modern Python CLI application."""
    pass


@app.command()
def start(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Start app mode (daemon)."""
    # Load configuration
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # Setup logging
    if verbose:
        log_level = "DEBUG"

    log_file = Path("logs") / f"{settings.app.name}.log"
    setup_logger(
        level=log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    logger.info(f"Starting {settings.app.name} in app mode")
    logger.info(f"Environment: {env}")
    logger.info(f"Debug mode: {settings.app.debug}")

    # Run app
    from src.utils.app_runner import run_app

    asyncio.run(run_app(settings))


@app.command()
def batch(
    env: str = typer.Option("dev", "--env", "-e", help="Environment (dev/prod)"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Log level"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Run batch mode (one-shot)."""
    # Load configuration
    if config:
        config_dir = Path(config).parent
        settings = load_config(env=env, config_dir=config_dir)
    else:
        settings = load_config(env=env)

    # Setup logging
    if verbose:
        log_level = "DEBUG"

    log_file = Path("logs") / f"{settings.app.name}_batch.log"
    setup_logger(
        level=log_level,
        log_file=log_file,
        format_str=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    logger.info(f"Starting {settings.app.name} in batch mode")
    logger.info(f"Environment: {env}")

    # Run batch
    from src.utils.batch_runner import run_batch

    asyncio.run(run_batch(settings))


if __name__ == "__main__":
    app()
```

**Step 5: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_main.py -v
```

Expected: All tests PASS

**Step 6: Test CLI manually**

Run:
```bash
uv run python -m src.main --version
uv run python -m src.main --help
```

Expected: Version and help displayed

**Step 7: Commit**

```bash
git add src/main.py src/core/ tests/test_main.py tests/test_core/
git commit -m "feat: add typer CLI entry point with start/batch commands"
```

---

## Task 11: Test Fixtures

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Write comprehensive fixtures**

Create `tests/conftest.py`:

```python
"""Pytest configuration and shared fixtures."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.utils.config import Settings


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
```

**Step 2: Run all tests to verify fixtures work**

Run:
```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add comprehensive pytest fixtures"
```

---

## Task 12: Pre-commit Configuration

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Create pre-commit config**

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-pyyaml
        args: [--strict]

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (fast tests only)
        entry: bash -c 'uv run pytest tests/test_utils/ -v --maxfail=1'
        language: system
        pass_filenames: false
        always_run: true
```

**Step 2: Install pre-commit hooks**

Run:
```bash
uv run pre-commit install
```

Expected: Hooks installed

**Step 3: Test pre-commit**

Run:
```bash
uv run pre-commit run --all-files
```

Expected: All hooks pass

**Step 4: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit configuration"
```

---

## Task 13: Documentation

**Files:**
- Create: `docs/FRAMEWORK_GUIDE.md`

**Step 1: Write framework guide**

Create `docs/FRAMEWORK_GUIDE.md`:

```markdown
# JPPT Framework Guide

This guide explains how to use the JPPT template for your projects.

## Quick Start

### 1. Create New Project from Template

\`\`\`bash
# Clone template
git clone <template-url> my-new-project
cd my-new-project

# Remove template git history
rm -rf .git
git init

# Install dependencies
uv sync --all-extras

# Copy example config
cp config/dev.yaml.example config/dev.yaml
\`\`\`

### 2. Configure Your Application

Edit `config/dev.yaml`:

\`\`\`yaml
app:
  name: "my-app"  # Change this
  debug: true

telegram:
  enabled: true
  # Set these via environment variables
\`\`\`

Set secrets:
\`\`\`bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
\`\`\`

### 3. Implement Business Logic

Choose your execution mode:

#### App Mode (Daemon)

Edit `src/utils/app_runner.py`:

\`\`\`python
async def run_app(settings: Settings) -> None:
    shutdown = GracefulShutdown()
    setup_signal_handlers(shutdown)

    # Initialize resources
    telegram = TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        enabled=settings.telegram.enabled,
    )

    # Register cleanup
    async def cleanup() -> None:
        logger.info("Cleaning up...")
        # Close connections, save state, etc.

    shutdown.register_cleanup(cleanup)

    # Main loop
    async with shutdown:
        await telegram.send_message("🚀 App started")

        while not shutdown.should_exit:
            try:
                # Your logic here
                await process_data()
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error: {e}")
                await telegram.send_error(e)

        await telegram.send_message("👋 App stopped")
\`\`\`

#### Batch Mode (One-Shot)

Edit `src/utils/batch_runner.py`:

\`\`\`python
async def run_batch(settings: Settings) -> None:
    logger.info("Starting batch job")

    # Your logic here
    results = await process_batch_data()

    logger.info(f"Batch complete: {results}")
\`\`\`

### 4. Add Your Business Logic

Create modules in `src/core/`:

\`\`\`python
# src/core/processor.py
from loguru import logger

async def process_data() -> dict:
    """Your business logic."""
    logger.info("Processing data")
    # Implementation
    return {"status": "success"}
\`\`\`

### 5. Write Tests

\`\`\`python
# tests/test_core/test_processor.py
import pytest
from src.core.processor import process_data

@pytest.mark.asyncio
async def test_process_data() -> None:
    result = await process_data()
    assert result["status"] == "success"
\`\`\`

### 6. Run Your Application

\`\`\`bash
# Development mode
uv run python -m src.main start --env dev --verbose

# Production mode
uv run python -m src.main start --env prod

# Batch mode
uv run python -m src.main batch --env dev
\`\`\`

## Architecture Overview

### Directory Structure

\`\`\`
src/
├── main.py              # CLI entry point (DON'T MODIFY MUCH)
├── core/                # YOUR BUSINESS LOGIC GOES HERE
│   └── *.py
└── utils/               # Framework utilities (modify carefully)
    ├── config.py        # Settings management
    ├── logger.py        # Logging setup
    ├── app_runner.py    # App mode (IMPLEMENT YOUR LOGIC)
    ├── batch_runner.py  # Batch mode (IMPLEMENT YOUR LOGIC)
    ├── exceptions.py    # Error types
    ├── retry.py         # Retry decorator
    ├── signals.py       # Graceful shutdown
    ├── http_client.py   # HTTP utilities
    └── telegram.py      # Notifications
\`\`\`

### What to Modify

**Always modify:**
- `src/core/` - Your business logic
- `src/utils/app_runner.py` - App mode implementation
- `src/utils/batch_runner.py` - Batch mode implementation
- `config/dev.yaml` - Your config
- `tests/test_core/` - Your tests

**Rarely modify:**
- `src/main.py` - CLI interface (only add commands)
- `src/utils/*.py` - Framework utilities (extend if needed)

**Never modify:**
- `pyproject.toml` dependencies (only add new ones)
- `ruff.toml`, `.pre-commit-config.yaml` (unless team decision)

## Common Patterns

### Using HTTP Client

\`\`\`python
from src.utils.http_client import HttpClient
from src.utils.retry import with_retry

@with_retry(max_attempts=3)
async def fetch_data(url: str) -> dict:
    async with HttpClient(base_url=url) as client:
        response = await client.get("/api/data")
        return response.json()
\`\`\`

### Error Handling

\`\`\`python
from src.utils.exceptions import ValidationError

def validate_input(data: dict) -> None:
    if "required_field" not in data:
        raise ValidationError("Missing required_field")
\`\`\`

### Logging

\`\`\`python
from loguru import logger

logger.debug("Detailed info")
logger.info("Normal operation")
logger.warning("Something unusual")
logger.error("Error occurred")
logger.exception("Error with traceback")
\`\`\`

### Telegram Notifications

\`\`\`python
from src.utils.telegram import TelegramNotifier

telegram = TelegramNotifier(
    bot_token=settings.telegram.bot_token,
    chat_id=settings.telegram.chat_id,
    enabled=settings.telegram.enabled,
)

await telegram.send_message("✅ Task completed")
await telegram.send_error(exception, context="Processing batch")
\`\`\`

## Testing Strategy

### Test Structure

\`\`\`
tests/
├── conftest.py          # Shared fixtures
├── test_main.py         # CLI tests
├── test_core/           # Your business logic tests
│   └── test_*.py
└── test_utils/          # Framework tests (rarely modify)
    └── test_*.py
\`\`\`

### Writing Tests

\`\`\`python
@pytest.mark.asyncio
async def test_my_feature(config: Settings, mock_telegram: MagicMock) -> None:
    # Arrange
    input_data = {"test": "data"}

    # Act
    result = await my_function(input_data)

    # Assert
    assert result["status"] == "success"
    mock_telegram.send_message.assert_called_once()
\`\`\`

### Running Tests

\`\`\`bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific test
uv run pytest tests/test_core/test_processor.py -v

# Watch mode (requires pytest-watch)
uv run ptw tests/
\`\`\`

## Configuration Management

### Layered Configuration

1. `config/default.yaml` - Base values (committed)
2. `config/{env}.yaml` - Environment overrides (gitignored)
3. Environment variables - Secrets (never committed)

### Adding New Settings

1. Update `config/default.yaml`:

\`\`\`yaml
my_feature:
  enabled: true
  api_url: "https://api.example.com"
\`\`\`

2. Update `src/utils/config.py`:

\`\`\`python
class MyFeatureConfig(BaseModel):
    enabled: bool = Field(default=True)
    api_url: str = Field(default="https://api.example.com")

class Settings(BaseSettings):
    # ... existing fields
    my_feature: MyFeatureConfig = Field(default_factory=MyFeatureConfig)
\`\`\`

3. Use in code:

\`\`\`python
if settings.my_feature.enabled:
    client = HttpClient(base_url=settings.my_feature.api_url)
\`\`\`

## Development Workflow

### 1. Create Feature Branch

\`\`\`bash
git checkout -b feature/my-feature
\`\`\`

### 2. Write Failing Test

\`\`\`bash
# Edit tests/test_core/test_my_feature.py
uv run pytest tests/test_core/test_my_feature.py -v
# Should FAIL
\`\`\`

### 3. Implement Feature

\`\`\`bash
# Edit src/core/my_feature.py
uv run pytest tests/test_core/test_my_feature.py -v
# Should PASS
\`\`\`

### 4. Run All Checks

\`\`\`bash
uv run pytest                    # Tests
uv run mypy src/                 # Type check
uv run ruff format .             # Format
uv run ruff check --fix .        # Lint
\`\`\`

### 5. Commit

\`\`\`bash
git add .
git commit -m "feat: add my feature"
# Pre-commit hooks run automatically
\`\`\`

## Deployment

### Using uv (Recommended)

\`\`\`bash
# Build wheel
uv build

# Deploy and run
uv sync --frozen
uv run python -m src.main start --env prod
\`\`\`

### Using systemd (Linux)

Create `/etc/systemd/system/my-app.service`:

\`\`\`ini
[Unit]
Description=My JPPT Application
After=network.target

[Service]
Type=simple
User=myuser
WorkingDirectory=/opt/my-app
Environment="TELEGRAM_BOT_TOKEN=xxx"
Environment="TELEGRAM_CHAT_ID=yyy"
ExecStart=/opt/my-app/.venv/bin/python -m src.main start --env prod
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
\`\`\`

Enable:
\`\`\`bash
sudo systemctl enable my-app
sudo systemctl start my-app
sudo systemctl status my-app
\`\`\`

## Troubleshooting

### "Module not found" errors

\`\`\`bash
uv sync --all-extras
\`\`\`

### Type check failures

\`\`\`bash
uv run mypy src/ --show-error-codes
\`\`\`

### Tests failing

\`\`\`bash
uv run pytest -vv --tb=short
\`\`\`

### Pre-commit blocking commits

\`\`\`bash
# Fix issues
uv run ruff format .
uv run ruff check --fix .
uv run mypy src/

# Or skip (not recommended)
git commit --no-verify
\`\`\`

## Tips

1. **Keep `core/` simple** - Business logic only
2. **Use type hints** - mypy strict mode is your friend
3. **Write tests first** - TDD saves time
4. **Small commits** - Easy to review and revert
5. **Log liberally** - But not secrets
6. **Graceful degradation** - Telegram fails? Log it, don't crash
7. **Config over code** - Put values in YAML
8. **DRY** - Don't repeat yourself
9. **YAGNI** - You aren't gonna need it
10. **Trust the framework** - Don't reinvent wheels

## Getting Help

- Check `docs/PRD.md` for architecture decisions
- Read source code in `src/utils/` for examples
- Look at existing tests for patterns
- Use `logger.debug()` liberally during development

Happy coding! 🚀
```

**Step 2: Commit**

```bash
git add docs/FRAMEWORK_GUIDE.md
git commit -m "docs: add comprehensive framework guide"
```

---

## Task 14: Final Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for the full application."""
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.main import app

runner = CliRunner()


def test_full_cli_integration(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full CLI workflow with config."""
    # Set environment variables
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    # Test version
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0

    # Test help
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout


@pytest.mark.asyncio
async def test_config_logger_integration(temp_config_dir: Path) -> None:
    """Test config and logger working together."""
    from src.utils.config import load_config
    from src.utils.logger import setup_logger

    config = load_config(env="dev", config_dir=temp_config_dir)

    log_file = temp_config_dir / "test.log"
    setup_logger(
        level=config.logging.level,
        log_file=log_file,
        format_str=config.logging.format,
    )

    from loguru import logger
    logger.info("Integration test")

    assert log_file.exists()
    assert "Integration test" in log_file.read_text()
```

**Step 2: Run integration tests**

Run:
```bash
uv run pytest tests/test_integration.py -v
```

Expected: All tests PASS

**Step 3: Run full test suite with coverage**

Run:
```bash
uv run pytest --cov=src --cov-report=term-missing --cov-report=html -v
```

Expected: All tests PASS, coverage > 80%

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full workflow"
```

---

## Task 15: Final Verification

**Step 1: Run all quality checks**

Run:
```bash
# Tests
uv run pytest -v

# Coverage
uv run pytest --cov=src --cov-report=term-missing

# Type check
uv run mypy src/

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .
```

Expected: All checks PASS

**Step 2: Test manual CLI execution**

Run:
```bash
# Help
uv run python -m src.main --help

# Version
uv run python -m src.main --version

# Batch mode (should complete)
uv run python -m src.main batch --verbose

# App mode (Ctrl+C to stop)
uv run python -m src.main start --verbose
```

Expected: All commands work

**Step 3: Verify file structure**

Run:
```bash
tree -L 3 -I '__pycache__|*.pyc|.venv|.git|htmlcov'
```

Expected: Matches PRD structure

**Step 4: Create final commit**

```bash
git add .
git commit -m "chore: final verification and cleanup"
```

**Step 5: Tag release**

```bash
git tag v0.1.0
git log --oneline
```

---

## Completion Checklist

- [ ] All tasks completed
- [ ] All tests passing (coverage > 80%)
- [ ] mypy strict mode passing
- [ ] ruff checks passing
- [ ] Pre-commit hooks working
- [ ] Manual CLI testing successful
- [ ] Documentation complete
- [ ] Git history clean with meaningful commits

## Next Steps

After completing this plan:

1. **Customize for your use case:**
   - Implement `src/core/` business logic
   - Update `src/utils/app_runner.py` with your app loop
   - Update `src/utils/batch_runner.py` with your batch logic

2. **Configure for deployment:**
   - Set up `config/prod.yaml`
   - Configure systemd/supervisor/docker
   - Set production environment variables

3. **Extend as needed:**
   - Add database integration (Supabase, etc.)
   - Add scheduler (APScheduler)
   - Add monitoring/metrics
   - Add web dashboard (Streamlit)

Refer to `docs/FRAMEWORK_GUIDE.md` for usage patterns and best practices.
