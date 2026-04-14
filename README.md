# JPPT - JKLEE Python Project Template

Modern Python CLI application template with best practices built-in.

## Features

- 🎯 **Typer CLI**: Clean command-line interface
- ⚙️ **Pydantic Settings**: Type-safe configuration with layered YAML
- 📝 **Loguru**: Structured logging with date-based rotation (`_YYYYMMDD.log`)
- 🔄 **Tenacity**: Retry logic with exponential backoff
- 📱 **Telegram**: Built-in notifications with interactive setup
- 🌐 **httpx**: Async HTTP client with timeout and error handling
- 🧪 **pytest**: 80% coverage requirement
- 🔍 **mypy**: Strict type checking
- ✨ **ruff**: Fast linting and formatting

## Quick Start

### Creating a New Project

**Linux/macOS:**
```bash
# Create new project from template
./scripts/create_app.sh my-awesome-app

# Or with options
./scripts/create_app.sh my-app --skip-tests  # Skip initial tests
./scripts/create_app.sh my-app --no-hooks    # Skip pre-commit hooks
```

This will:
- ✅ Verify Python 3.11+, uv, and GitHub CLI installation
- ✅ Validate app name (lowercase, numbers, hyphens, underscores only)
- ✅ Create new project directory (`../my-app`)
- ✅ Copy template with proper exclusions
- ✅ Update project name in config files (`dev.yaml`, `dev.yaml.example`, `prod.yaml.example`, `pyproject.toml`)
- ✅ Create `README.md` and `docs/PRD.md` for new project
- ✅ Initialize git repository with initial commit
- ✅ Create private GitHub repository and push
- ✅ Install all dependencies
- ✅ Set up configuration files (`dev.yaml`)
- ✅ **Interactive Telegram setup** (auto-fetches Chat IDs from API)
- ✅ Install pre-commit hooks (optional)
- ✅ Run initial tests (optional)

### Setting Up JPPT Template Itself

If you want to work on the JPPT template itself (not create a new project):

**Linux/macOS:**
```bash
cd JPPT  # Navigate to JPPT directory
uv sync --all-extras
cp config/dev.yaml.example config/dev.yaml
```

### Run the Application

**Linux/macOS:**
```bash
# Quick run scripts (recommended)
./run.sh              # Start mode, dev environment
./run.sh batch        # Batch mode, dev environment
./run.sh start prod   # Start mode, prod environment
```

**Or use uv directly (all platforms):**
```bash
uv run python -m src.main start --env dev
uv run python -m src.main batch --env dev
```

### Development Commands

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

## Architecture

### System Architecture

```mermaid
graph TB
    subgraph CLI["🎯 CLI Layer"]
        TYPER["main.py<br/>(Typer)"]
    end

    subgraph CONFIG["⚙️ Configuration"]
        YAML["YAML Files<br/>(default / dev / prod)"]
        PYDANTIC["Pydantic Settings<br/>(config.py)"]
        ENV["Environment Variables"]
    end

    subgraph CORE["🧩 Core Layer"]
        APP["App Runner<br/>(Long-running daemon)"]
        BATCH["Batch Runner<br/>(One-shot execution)"]
        BIZ["Business Logic<br/>(core/)"]
    end

    subgraph UTILS["🔧 Utilities"]
        LOGGER["Loguru Logger"]
        RETRY["Retry<br/>(Tenacity)"]
        SIGNALS["Graceful Shutdown<br/>(Signal Handler)"]
        HTTP["HTTP Client<br/>(httpx)"]
        TELEGRAM["Telegram Notifier"]
        EXCEPTIONS["Exception Hierarchy"]
    end

    TYPER -->|start| APP
    TYPER -->|batch| BATCH
    YAML --> PYDANTIC
    ENV --> PYDANTIC
    PYDANTIC --> TYPER
    APP --> BIZ
    BATCH --> BIZ
    BIZ --> LOGGER
    BIZ --> RETRY
    BIZ --> HTTP
    BIZ --> TELEGRAM
    APP --> SIGNALS
    HTTP --> RETRY
    TELEGRAM --> HTTP
    RETRY --> EXCEPTIONS
    HTTP --> EXCEPTIONS
```

### Execution Flow

```mermaid
flowchart TD
    START(["🚀 User runs CLI"]) --> PARSE["Parse arguments<br/>(Typer)"]
    PARSE --> LOAD_CONFIG["Load configuration<br/>(config/{env}.yaml + env vars)"]
    LOAD_CONFIG --> SETUP_LOG["Setup Loguru logger<br/>(console + file)"]
    SETUP_LOG --> MODE{Mode?}

    MODE -->|"start"| APP_INIT["Initialize GracefulShutdown<br/>Register signal handlers"]
    APP_INIT --> APP_RESOURCES["Initialize resources<br/>(HTTP Client, Telegram, etc.)"]
    APP_RESOURCES --> APP_LOOP["Main async loop<br/>(while not should_exit)"]
    APP_LOOP -->|"Signal received<br/>(Ctrl+C / SIGTERM)"| CLEANUP["Run cleanup callbacks"]
    CLEANUP --> EXIT_OK(["✅ Exit 0"])

    MODE -->|"batch"| BATCH_RUN["Execute business logic<br/>(one-shot)"]
    BATCH_RUN --> EXIT_OK

    APP_LOOP -->|"Exception"| ERROR_HANDLE["Error handling<br/>+ Telegram notification"]
    ERROR_HANDLE --> EXIT_FAIL(["❌ Exit 1"])
    BATCH_RUN -->|"Exception"| EXIT_FAIL
```

### Configuration Loading

```mermaid
%% TODO(human): Design the configuration loading flow diagram
%% Show single-file env config loading plus optional environment-variable overrides
%% Include which files are committed templates vs gitignored runtime configs
```

## Project Structure

```
src/
├── main.py              # CLI entry point
├── core/                # Business logic
└── utils/               # Reusable utilities
    ├── config.py        # Settings management (Pydantic)
    ├── logger.py        # Logging setup (Loguru)
    ├── app_runner.py    # App mode (daemon)
    ├── batch_runner.py  # Batch mode (one-shot)
    ├── exceptions.py    # Custom exception hierarchy
    ├── retry.py         # Retry decorator (tenacity)
    ├── signals.py       # Graceful shutdown
    ├── http_client.py   # Async HTTP client (httpx)
    └── telegram.py      # Telegram notifications

scripts/                 # Automation scripts
└── create_app.sh        # Project generator (Linux/macOS)

run.sh                   # Quick run wrapper (Linux/macOS)

tests/                   # Test suite
config/                  # Configuration files
docs/                    # Documentation
```

## Configuration

### Environment Configuration System

Configuration is loaded from the selected environment file, with optional environment-variable overrides:

1. **`config/{env}.yaml`** — Environment-specific runtime config (gitignored)
2. **Environment variables** — Final overrides for secrets

```yaml
# config/dev.yaml
app:
  name: "jppt"
  version: "0.1.0"
  debug: true

logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
  rotation: "00:00"       # Daily rotation at midnight
  retention: "10 days"    # Keep logs for 10 days

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
```

Committed templates live in `config/dev.yaml.example` and `config/prod.yaml.example`; copy one to `config/{env}.yaml` before running.

### Telegram Setup

Telegram can be configured in two ways:

**1. Interactive setup (recommended):** During `create_app.sh`, the script will:
   - Ask for your Bot Token (get it from [@BotFather](https://t.me/BotFather))
   - Auto-fetch available Chat IDs from the Telegram API
   - Save settings directly to `config/dev.yaml`

**2. Environment variable override:**
   ```bash
   # Linux/macOS
   export TELEGRAM__BOT_TOKEN="your-token"
   export TELEGRAM__CHAT_ID="your-chat-id"
   ```
### Environment-Specific Config

```bash
# Development (auto-created by create_app.sh)
config/dev.yaml

# Production (create manually)
cp config/dev.yaml.example config/prod.yaml
# Edit prod.yaml with production settings
```

## Logging

Logs are written to the `$HOME/logs/` directory (user's home directory) with automatic date-based rotation:

- **Active log:** `$HOME/logs/{app_name}.log` (or `{app_name}_batch.log` for batch mode)
- **Rotated logs:** `$HOME/logs/{app_name}_YYYYMMDD.log` (e.g., `myapp_20260206.log`)
- **Rotation:** Daily at midnight (configurable)
- **Retention:** 10 days by default (configurable)

**Note:** Logs are stored in your home directory (`~/logs/`) to keep the project directory clean and centralize logs across multiple projects.

## Scripts

### Project Generator (`scripts/create_app.sh`)

Creates a new project from the JPPT template.

**Linux/macOS:**
```bash
./scripts/create_app.sh <app-name> [OPTIONS]
./scripts/create_app.sh --help    # Show options
```

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-tests` | Skip running initial tests |
| `--no-hooks` | Skip pre-commit hooks installation |
| `--help` | Show usage information |

**Requirements:**
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Package manager
- [GitHub CLI](https://cli.github.com/) — Repository creation (`gh auth login` required)

### Run Scripts

Quick run wrappers — simplified app execution.

**Linux/macOS (`run.sh`):**
```bash
./run.sh [MODE] [ENV]
./run.sh --help           # Show usage

# Examples:
./run.sh                  # start mode, dev env
./run.sh batch            # batch mode, dev env
./run.sh start prod       # start mode, prod env
```

## Examples and Patterns

### Core Structure Patterns

Learn how to structure `src/core/` for complex applications:
- 📚 **[Core Structure Patterns Guide](docs/examples/core-structure-patterns.md)**
  - Data source integration pattern (multi-source, ABC interfaces)
  - Output renderer pattern (terminal, CSV, JSON)
  - Business logic engine pattern
  - Pydantic model patterns

### Real-World Example: KAVS

**[KAVS](https://github.com/taein2301/kavs)** - Korean Automated Value Screening

A production CLI tool built with JPPT that demonstrates:
- Multi-source data integration (KRX, OpenDART APIs)
- ABC pattern for pluggable data sources
- Rich terminal output with tables
- Screening engine with filtering logic
- 80%+ test coverage

Check out the [KAVS source code](https://github.com/taein2301/kavs) to see these patterns in action!

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
