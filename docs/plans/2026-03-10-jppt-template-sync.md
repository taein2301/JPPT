# JPPT Template Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Port template-common infrastructure improvements from `jupbc-cat` into existing `JPPT` files only.

**Architecture:** Keep `JPPT`'s current module layout and selectively merge behavior-level improvements into overlapping files. Avoid importing product-specific runtime dependencies or adding new modules.

**Tech Stack:** Python, Typer, Loguru, Pydantic Settings, Bash, pytest

---

### Task 1: Add failing tests for shared CLI/logging/config/notifier behavior

**Files:**
- Modify: `tests/test_main.py`
- Modify: `tests/test_utils/test_config.py`
- Modify: `tests/test_utils/test_logger.py`
- Modify: `tests/test_utils/test_telegram.py`

**Step 1: Write the failing tests**

Add tests for:
- CLI `--log-level` override behavior
- CLI startup config-summary logging
- logger console-format helper / `json_logs`
- config defaults including `logging.json_logs`
- Telegram timeout warning behavior

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py tests/test_utils/test_config.py tests/test_utils/test_logger.py tests/test_utils/test_telegram.py`
Expected: FAIL because the new behavior is not implemented yet.

### Task 2: Implement the minimal shared runtime changes

**Files:**
- Modify: `src/main.py`
- Modify: `src/utils/logger.py`
- Modify: `src/utils/config.py`
- Modify: `src/utils/telegram.py`
- Modify: `config/dev.yaml.example`
- Modify: `config/prod.yaml.example`
- Modify: `run.sh`
- Modify: `scripts/create_app.sh`

**Step 1: Write minimal implementation**

Implement only the behavior required by the failing tests and selected scope:
- CLI effective log-level resolution and startup summary logging
- logger `json_logs` support and safe console format helper
- config model support for `logging.json_logs`
- Telegram timeout warning handling
- example config updates
- `run.sh` log-path/help output fixes
- `scripts/create_app.sh` GitHub repo-scope validation

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_main.py tests/test_utils/test_config.py tests/test_utils/test_logger.py tests/test_utils/test_telegram.py`
Expected: PASS

### Task 3: Run final verification for touched integration surface

**Files:**
- Modify: `tests/test_integration.py` only if required by behavior changes

**Step 1: Run broader verification**

Run: `uv run pytest tests/test_main.py tests/test_integration.py tests/test_utils/test_config.py tests/test_utils/test_logger.py tests/test_utils/test_telegram.py`
Expected: PASS
