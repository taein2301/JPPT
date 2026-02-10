# CLAUDE.md — AI Assistant Guide for JPPT

## Project Overview

**JPPT** (JKLEE Python Project Template) is a production-ready Python CLI application template. It provides a fully wired starter kit for building Python CLI tools with async support, layered YAML configuration, structured logging, HTTP client, Telegram notifications, and graceful shutdown.

- **Language:** Python 3.11+
- **Package manager:** uv (Astral)
- **Build backend:** hatchling
- **CLI framework:** Typer
- **Primary language in comments/docstrings:** Korean (한국어)

## Quick Reference — Commands

```bash
# Install dependencies (including dev)
uv sync --dev

# Run the app (start mode — daemon)
uv run python -m src.main start --env dev

# Run the app (batch mode — one-shot)
uv run python -m src.main batch --env dev

# Run tests with coverage (80% minimum required)
uv run pytest

# Run tests without coverage
uv run pytest --no-cov

# Run a single test file
uv run pytest tests/test_main.py

# Lint (check only)
uv run ruff check src tests

# Lint (auto-fix)
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests

# Type check
uv run mypy src --exclude src/logs

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Project Structure

```
JPPT/
├── src/                        # Application source (hatchling package root)
│   ├── main.py                 # CLI entry point (Typer app with `start` and `batch` commands)
│   ├── core/                   # Business logic (empty template — user implements here)
│   │   └── __init__.py
│   └── utils/                  # Reusable infrastructure utilities
│       ├── config.py           # Layered YAML config with Pydantic validation
│       ├── logger.py           # Loguru setup with daily rotation
│       ├── app_runner.py       # Daemon mode (async loop + graceful shutdown)
│       ├── batch_runner.py     # One-shot execution mode
│       ├── exceptions.py       # Custom exception hierarchy
│       ├── signals.py          # GracefulShutdown + SIGTERM/SIGINT handlers
│       ├── http_client.py      # Async httpx wrapper (context manager)
│       ├── telegram.py         # Telegram bot notifier
│       └── retry.py            # @with_retry decorator (tenacity + exponential backoff)
├── tests/                      # Test suite (mirrors src/ structure)
│   ├── conftest.py             # Shared fixtures
│   ├── test_main.py            # CLI command tests
│   ├── test_utils/             # Unit tests for each utility module
│   ├── test_core/              # Tests for business logic
│   └── test_integration.py    # Integration tests (uses httpbin.org)
├── config/                     # YAML configuration files
│   ├── default.yaml            # Base config (committed)
│   └── dev.yaml.example        # Dev override template (committed)
├── scripts/                    # Project generation scripts
│   ├── create_app.sh           # Create new project from template (Linux/macOS)
│   └── create_app.ps1          # Create new project from template (Windows)
├── docs/                       # Documentation and planning
├── pyproject.toml              # Project metadata, dependencies, tool config
├── ruff.toml                   # Ruff linter/formatter config
├── .pre-commit-config.yaml     # Pre-commit hooks (ruff + mypy)
├── run.sh / run.ps1            # Quick-start runners
└── uv.lock                     # Locked dependencies
```

## Architecture & Key Patterns

### Configuration System
Each environment has its own complete configuration file:
- `config/dev.yaml` — development environment config (gitignored)
- `config/prod.yaml` — production environment config (gitignored)
- `config/{env}.yaml.example` — template files (committed)

All config is validated through Pydantic models in `src/utils/config.py`.
Use `--env` flag to select which config to load (defaults to `dev`).

### Execution Modes
- **Start (daemon):** `src/utils/app_runner.py` — async loop with `GracefulShutdown` context manager. Runs until SIGTERM/SIGINT.
- **Batch (one-shot):** `src/utils/batch_runner.py` — runs once and exits. For cron/schedulers.

### Exception Hierarchy
```
AppException
├── ConfigurationError
├── ServiceError
│   ├── TelegramError
│   └── HttpClientError
├── ValidationError
└── RetryExhaustedError
```
Always use the appropriate custom exception from `src/utils/exceptions.py`. Do not raise bare `Exception`.

### Async Context Managers
`HttpClient` and `GracefulShutdown` are async context managers. Always use them with `async with`:
```python
async with HttpClient(base_url="https://api.example.com") as client:
    response = await client.get("/endpoint")
```

## Code Style & Conventions

### Formatting (enforced by ruff)
- **Line length:** 100 characters
- **Quote style:** double quotes (`"`)
- **Indent style:** spaces
- **Target:** Python 3.11

### Lint Rules (ruff)
Selected rule sets: `E, F, I, N, W, UP, B, C4, SIM` (ignore `N818`)

### Type Checking (mypy strict mode)
- `strict = true` — all functions must have type annotations
- `disallow_untyped_defs = true`
- `disallow_any_unimported = true`
- `no_implicit_optional = true`
- Module override: `telegram.*` has `ignore_missing_imports = true`

### Import Convention
Use absolute imports from `src`:
```python
from src.utils.config import load_config, Settings
from src.utils.exceptions import AppException, ConfigurationError
from src.utils.http_client import HttpClient
```

### Docstrings & Comments
- Docstrings and inline comments are written in **Korean (한국어)**
- Module-level docstrings describe the module's purpose
- Class/function docstrings use Google-style with Korean descriptions
- `Args`, `Returns`, `Raises` sections use English keywords with Korean explanations

### Type Hints
- Use modern Python 3.11+ syntax: `str | None` (not `Optional[str]`), `dict[str, Any]` (not `Dict`)
- All public functions must be fully type-annotated
- Use `TypeVar` for generic return types in decorators

## Testing Conventions

### Running Tests
```bash
uv run pytest                          # Full suite with coverage
uv run pytest tests/test_main.py       # Single file
uv run pytest -k "test_version"        # By name pattern
```

### Configuration (from pyproject.toml)
- **pythonpath:** `["src"]`
- **testpaths:** `["tests"]`
- **Coverage minimum:** 80% (`--cov-fail-under=80`)
- **asyncio_mode:** `auto` (no need for `@pytest.mark.asyncio`)
- **Markers:** strict mode — all markers must be declared

### Test Structure
- Test files mirror source: `src/utils/config.py` → `tests/test_utils/test_config.py`
- Shared fixtures in `tests/conftest.py`: `sample_config`, `config`, `mock_telegram`, `mock_http_client`, `temp_config_dir`
- Use `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`) for mocking
- Integration tests in `tests/test_integration.py` make real HTTP calls to httpbin.org

### Writing New Tests
- Name files `test_*.py`, classes `Test*`, functions `test_*`
- Use existing fixtures from conftest.py when possible
- Mock external services; don't add network dependencies in unit tests

## Git Conventions

### Ignored Files (do NOT commit)
- `config/dev.yaml`, `config/prod.yaml` — environment-specific secrets
- `logs/`, `*.log` — runtime logs
- `.venv/`, `__pycache__/`, `.pytest_cache/`

### Merge Strategy (.gitattributes)
These files use `merge=ours` to preserve app-specific customizations when pulling from the template upstream:
- `src/core/**`
- `src/utils/app_runner.py`, `src/utils/batch_runner.py`
- `config/*.yaml`
- `README.md`

### Pre-commit Hooks
Three hooks run automatically on commit:
1. **ruff** — lint with auto-fix
2. **ruff-format** — code formatting
3. **mypy** — strict type checking on `src/`

## Where to Add New Code

- **Business logic:** `src/core/` — this is the intended extension point
  - See `docs/examples/core-structure-patterns.md` for recommended patterns:
    - **Data source pattern**: `src/core/data/` with ABC interfaces
    - **Renderer pattern**: `src/core/output/` for different output formats
    - **Engine pattern**: Main processing logic with aggregators
    - **Model pattern**: Pydantic models in `src/core/models.py`
- **New utility:** `src/utils/` — for reusable infrastructure components
- **New CLI command:** `src/main.py` — add a new `@app.command()` function
- **New config section:** Add a Pydantic `BaseModel` in `src/utils/config.py`, then add the field to `Settings`
- **New tests:** Mirror the source path under `tests/`

### Recommended `src/core/` Structure

For complex applications, organize `src/core/` with these patterns:

```
src/core/
├── models.py            # Pydantic data models
├── engine.py            # Main business logic
├── data/                # Data source integration
│   ├── base.py          # ABC interfaces
│   ├── source_a.py      # Source implementations
│   └── aggregator.py    # Multi-source integration
└── output/              # Output renderers
    ├── terminal_renderer.py
    └── csv_renderer.py
```

See the [KAVS project](https://github.com/taein2301/kavs) for a real-world example of these patterns in action.

## Common Pitfalls

- Always run `uv sync --dev` after pulling — this project uses uv, not pip
- The config system requires `config/default.yaml` to exist; missing it raises `ConfigurationError`
- `HttpClient` must be used as an async context manager (`async with`) or you'll get `"Client not initialized"` errors
- mypy is in strict mode: forgetting type annotations will fail the pre-commit hook
- Test coverage must stay at or above 80% — new code without tests will fail CI
