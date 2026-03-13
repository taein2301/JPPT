# FastAPI Template Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the existing FastAPI skeleton so the JPPT template provides production-ready API defaults with consistent configuration and documentation.

**Architecture:** Keep the current CLI-first project shape, but formalize an `api` settings section, use an app factory with routers and exception handlers, and add middleware/lifespan behavior that templates can extend without rewriting the foundation.

**Tech Stack:** Python, FastAPI, Uvicorn, Typer, Pydantic Settings, pytest

---

### Task 1: Lock behavior with failing tests

**Files:**
- Modify: `tests/test_utils/test_config.py`
- Modify: `tests/test_api.py`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

Add tests for:
- layered config loading from `default.yaml` plus `{env}.yaml`
- `api` settings defaults and env-specific overrides
- `/ready` endpoint, OpenAPI docs toggle, and error-response structure
- CLI `api` command forwarding host/port/reload from settings when omitted

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_api.py tests/test_main.py --no-cov`
Expected: FAIL because the new behavior is not implemented yet.

### Task 2: Implement minimal FastAPI template foundation

**Files:**
- Modify: `src/utils/config.py`
- Modify: `src/api/app.py`
- Modify: `src/utils/api_runner.py`
- Modify: `src/main.py`

**Step 1: Write minimal implementation**

Implement:
- `ApiConfig` model and layered YAML merge
- app factory with docs URLs based on debug mode
- shared exception handlers and request-id middleware
- `/health`, `/ready`, and sample `/jobs` behavior with tagged router structure
- API runner defaults that honor settings

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_api.py tests/test_main.py --no-cov`
Expected: PASS

### Task 3: Align examples and docs

**Files:**
- Modify: `config/dev.yaml.example`
- Modify: `config/prod.yaml.example`
- Modify: `README.md`
- Modify: `README.ko.md`

**Step 1: Update documentation**

Document:
- `api` command usage
- new `api` config section
- layered config behavior
- available API endpoints

**Step 2: Run broader verification**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_api.py tests/test_main.py tests/test_utils/test_exceptions.py --no-cov`
Expected: PASS
