# JPPT Framework Guide

This guide explains how to use the JPPT template for your projects.

## Quick Start

### 1. Create New Project from Template

```bash
# Clone template
git clone https://github.com/taein2301/JPPT.git my-new-project
cd my-new-project

# Remove template git history
rm -rf .git
git init

# Install dependencies
uv sync --all-extras

# Copy example config
cp config/dev.yaml.example config/dev.yaml
```

### 2. Configure Your Application

Edit `config/dev.yaml`:

```yaml
app:
  name: "my-app"  # Change this
  debug: true

telegram:
  enabled: true
  # Set these via environment variables
```

Set secrets:
```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### 3. Implement Business Logic

Choose your execution mode:

#### App Mode (Daemon)

Edit `src/utils/app_runner.py`:

```python
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
```

#### Batch Mode (One-Shot)

Edit `src/utils/batch_runner.py`:

```python
async def run_batch(settings: Settings) -> None:
    logger.info("Starting batch job")

    # Your logic here
    results = await process_batch_data()

    logger.info(f"Batch complete: {results}")
```

### 4. Add Your Business Logic

Create modules in `src/core/`:

```python
# src/core/processor.py
from loguru import logger

async def process_data() -> dict:
    """Your business logic."""
    logger.info("Processing data")
    # Implementation
    return {"status": "success"}
```

### 5. Write Tests

```python
# tests/test_core/test_processor.py
import pytest
from src.core.processor import process_data

@pytest.mark.asyncio
async def test_process_data() -> None:
    result = await process_data()
    assert result["status"] == "success"
```

### 6. Run Your Application

```bash
# Development mode
uv run python -m src.main start --env dev --verbose

# Production mode
uv run python -m src.main start --env prod

# Batch mode
uv run python -m src.main batch --env dev
```

## Architecture Overview

### Directory Structure

```
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
```

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

```python
from src.utils.http_client import HttpClient
from src.utils.retry import with_retry

@with_retry(max_attempts=3)
async def fetch_data(url: str) -> dict:
    async with HttpClient(base_url=url) as client:
        response = await client.get("/api/data")
        return response.json()
```

### Error Handling

```python
from src.utils.exceptions import ValidationError

def validate_input(data: dict) -> None:
    if "required_field" not in data:
        raise ValidationError("Missing required_field")
```

### Logging

```python
from loguru import logger

logger.debug("Detailed info")
logger.info("Normal operation")
logger.warning("Something unusual")
logger.error("Error occurred")
logger.exception("Error with traceback")
```

### Telegram Notifications

```python
from src.utils.telegram import TelegramNotifier

telegram = TelegramNotifier(
    bot_token=settings.telegram.bot_token,
    chat_id=settings.telegram.chat_id,
    enabled=settings.telegram.enabled,
)

await telegram.send_message("✅ Task completed")
await telegram.send_error(exception, context="Processing batch")
```

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_main.py         # CLI tests
├── test_core/           # Your business logic tests
│   └── test_*.py
└── test_utils/          # Framework tests (rarely modify)
    └── test_*.py
```

### Writing Tests

```python
@pytest.mark.asyncio
async def test_my_feature(config: Settings, mock_telegram: MagicMock) -> None:
    # Arrange
    input_data = {"test": "data"}

    # Act
    result = await my_function(input_data)

    # Assert
    assert result["status"] == "success"
    mock_telegram.send_message.assert_called_once()
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific test
uv run pytest tests/test_core/test_processor.py -v

# Watch mode (requires pytest-watch)
uv run ptw tests/
```

## Configuration Management

### Layered Configuration

1. `config/default.yaml` - Base values (committed)
2. `config/{env}.yaml` - Environment overrides (gitignored)
3. Environment variables - Secrets (never committed)

### Adding New Settings

1. Update `config/default.yaml`:

```yaml
my_feature:
  enabled: true
  api_url: "https://api.example.com"
```

2. Update `src/utils/config.py`:

```python
class MyFeatureConfig(BaseModel):
    enabled: bool = Field(default=True)
    api_url: str = Field(default="https://api.example.com")

class Settings(BaseSettings):
    # ... existing fields
    my_feature: MyFeatureConfig = Field(default_factory=MyFeatureConfig)
```

3. Use in code:

```python
if settings.my_feature.enabled:
    client = HttpClient(base_url=settings.my_feature.api_url)
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Write Failing Test

```bash
# Edit tests/test_core/test_my_feature.py
uv run pytest tests/test_core/test_my_feature.py -v
# Should FAIL
```

### 3. Implement Feature

```bash
# Edit src/core/my_feature.py
uv run pytest tests/test_core/test_my_feature.py -v
# Should PASS
```

### 4. Run All Checks

```bash
uv run pytest                    # Tests
uv run mypy src/                 # Type check
uv run ruff format .             # Format
uv run ruff check --fix .        # Lint
```

### 5. Commit

```bash
git add .
git commit -m "feat: add my feature"
# Pre-commit hooks run automatically
```

## Deployment

### Using uv (Recommended)

```bash
# Build wheel
uv build

# Deploy and run
uv sync --frozen
uv run python -m src.main start --env prod
```

### Using systemd (Linux)

Create `/etc/systemd/system/my-app.service`:

```ini
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
```

Enable:
```bash
sudo systemctl enable my-app
sudo systemctl start my-app
sudo systemctl status my-app
```

## Troubleshooting

### "Module not found" errors

```bash
uv sync --all-extras
```

### Type check failures

```bash
uv run mypy src/ --show-error-codes
```

### Tests failing

```bash
uv run pytest -vv --tb=short
```

### Pre-commit blocking commits

```bash
# Fix issues
uv run ruff format .
uv run ruff check --fix .
uv run mypy src/

# Or skip (not recommended)
git commit --no-verify
```

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
