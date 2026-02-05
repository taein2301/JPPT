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

**Linux/macOS:**
```bash
# One-command setup (recommended)
./scripts/create_app.sh

# Or setup with options
./scripts/create_app.sh --skip-tests  # Skip initial tests
./scripts/create_app.sh --no-hooks    # Skip pre-commit hooks
```

**Windows (PowerShell):**
```powershell
# One-command setup (recommended)
.\scripts\create_app.ps1

# Or setup with options
.\scripts\create_app.ps1 -SkipTests   # Skip initial tests
.\scripts\create_app.ps1 -NoHooks     # Skip pre-commit hooks
```

This will:
- ✅ Verify Python 3.11+ and uv installation
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Set up logging directories
- ✅ Install pre-commit hooks
- ✅ Run initial tests (optional)

### 2. Run the Application

**Linux/macOS:**
```bash
# Quick run scripts (recommended)
./scripts/run.sh              # Start mode, dev environment
./scripts/run.sh batch        # Batch mode, dev environment
./scripts/run.sh start prod   # Start mode, prod environment
```

**Windows (PowerShell):**
```powershell
# Quick run scripts (recommended)
.\scripts\run.ps1              # Start mode, dev environment
.\scripts\run.ps1 batch        # Batch mode, dev environment
.\scripts\run.ps1 start prod   # Start mode, prod environment
```

**Or use uv directly (all platforms):**
```bash
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
├── create_app.sh        # Initial setup script (Linux/macOS)
├── create_app.ps1       # Initial setup script (Windows)
├── run.sh               # Quick run wrapper (Linux/macOS)
└── run.ps1              # Quick run wrapper (Windows)

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

   **Linux/macOS:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:TELEGRAM_BOT_TOKEN="your-token"
   $env:TELEGRAM_CHAT_ID="your-chat-id"
   ```

4. For production, create `config/prod.yaml`:
   ```bash
   cp config/dev.yaml.example config/prod.yaml
   # Edit prod.yaml with production settings
   ```

## Scripts

### Setup Scripts

Initial setup scripts - run once after cloning the template.

**Linux/macOS (`scripts/create_app.sh`):**
```bash
./scripts/create_app.sh           # Full setup
./scripts/create_app.sh --help    # Show options
```

**Windows (`scripts/create_app.ps1`):**
```powershell
.\scripts\create_app.ps1          # Full setup
.\scripts\create_app.ps1 -Help    # Show options
```

**Features:**
- Validates Python 3.11+ and uv installation
- Installs all dependencies with `uv sync --all-extras`
- Creates `config/dev.yaml` from example
- Sets up `logs/` directory
- Installs pre-commit hooks
- Runs initial tests (optional)

### Run Scripts

Quick run wrappers - simplified app execution.

**Linux/macOS (`scripts/run.sh`):**
```bash
./scripts/run.sh [MODE] [ENV]
./scripts/run.sh --help           # Show usage

# Examples:
./scripts/run.sh                  # start mode, dev env
./scripts/run.sh batch            # batch mode, dev env
./scripts/run.sh start prod       # start mode, prod env
```

**Windows (`scripts/run.ps1`):**
```powershell
.\scripts\run.ps1 [MODE] [ENV]
.\scripts\run.ps1 -Help           # Show usage

# Examples:
.\scripts\run.ps1                 # start mode, dev env
.\scripts\run.ps1 batch           # batch mode, dev env
.\scripts\run.ps1 start prod      # start mode, prod env
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
