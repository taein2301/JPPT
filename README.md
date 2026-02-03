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

```bash
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
```

## Project Structure

```
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
```

## Configuration

1. Copy example config:
   ```bash
   cp config/dev.yaml.example config/dev.yaml
   ```

2. Edit `config/dev.yaml` with your settings

3. Set environment variables for secrets:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

## Development

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all checks
uv run pre-commit run --all-files
```

## License

MIT
