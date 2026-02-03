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

### 1. Initial Setup

```bash
# One-command setup (recommended)
./scripts/create_app.sh

# Or setup with options
./scripts/create_app.sh --skip-tests  # Skip initial tests
./scripts/create_app.sh --no-hooks    # Skip pre-commit hooks
```

This will:
- ✅ Verify Python 3.11+ and uv installation
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Set up logging directories
- ✅ Install pre-commit hooks
- ✅ Run initial tests (optional)

### 2. Run the Application

```bash
# Quick run scripts (recommended)
./scripts/run.sh              # Start mode, dev environment
./scripts/run.sh batch        # Batch mode, dev environment
./scripts/run.sh start prod   # Start mode, prod environment

# Or use uv directly
uv run python -m src.main start --env dev
uv run python -m src.main batch --env dev
```

### 3. Development Commands

```bash
# Run tests
uv run pytest

# Format code
uv run ruff format .

# Type check
uv run mypy src/

# Run all pre-commit checks
uv run pre-commit run --all-files
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

scripts/                 # Automation scripts
├── create_app.sh        # Initial setup script
└── run.sh               # Quick run wrapper

tests/                   # Test suite
config/                  # Configuration files
docs/                    # Documentation
```

## Configuration

Configuration is automatically set up by `./scripts/create_app.sh`, but you can also:

1. Manually copy example config:
   ```bash
   cp config/dev.yaml.example config/dev.yaml
   ```

2. Edit `config/dev.yaml` with your settings

3. Set environment variables for secrets:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

4. For production, create `config/prod.yaml`:
   ```bash
   cp config/dev.yaml.example config/prod.yaml
   # Edit prod.yaml with production settings
   ```

## Scripts

### `scripts/create_app.sh`

Initial setup script - run this once after cloning the template.

```bash
./scripts/create_app.sh           # Full setup
./scripts/create_app.sh --help    # Show options
```

**Features:**
- Validates Python 3.11+ and uv installation
- Installs all dependencies with `uv sync --all-extras`
- Creates `config/dev.yaml` from example
- Sets up `logs/` directory
- Installs pre-commit hooks
- Runs initial tests (optional)

### `scripts/run.sh`

Quick run wrapper - simplified app execution.

```bash
./scripts/run.sh [MODE] [ENV]
./scripts/run.sh --help           # Show usage
```

**Examples:**
```bash
./scripts/run.sh                  # start mode, dev env
./scripts/run.sh batch            # batch mode, dev env
./scripts/run.sh start prod       # start mode, prod env
./scripts/run.sh batch prod       # batch mode, prod env
```

**Features:**
- Validates uv and config file existence
- Clear execution info output
- Auto-creates logs directory
- Proper error messages and exit codes

## Development

Pre-commit hooks are automatically installed by `./scripts/create_app.sh`.

```bash
# Manually install hooks
uv run pre-commit install

# Run all checks
uv run pre-commit run --all-files
```

## License

MIT
