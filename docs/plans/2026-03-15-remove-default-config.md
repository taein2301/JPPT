# Remove default.yaml Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove `config/default.yaml` and make runtime configuration load directly from `config/dev.yaml` or `config/prod.yaml`.

**Architecture:** `load_config()` will read a single environment file and rely on Pydantic model defaults for omitted values. Tests and supporting docs/scripts will be updated to remove assumptions about a committed base config layer.

**Tech Stack:** Python 3.11, Pydantic Settings, PyYAML, pytest, Ruff

---

### Task 1: Reproduce single-file config loading expectations

**Files:**
- Modify: `tests/test_utils/test_config.py`
- Test: `tests/test_utils/test_config.py`

**Step 1: Write the failing test**

```python
def test_load_config_uses_env_file_only(tmp_path: Path) -> None:
    (tmp_path / "dev.yaml").write_text(
        '''
app:
  name: "test"
''',
        encoding="utf-8",
    )

    config = load_config(env="dev", config_dir=tmp_path)

    assert config.app.name == "test"
    assert config.app.version == "0.1.0"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_utils/test_config.py -k "env_file_only or missing_default_file" -v`
Expected: FAIL because `load_config()` still requires `default.yaml`

**Step 3: Write minimal implementation**

```python
config_file = config_dir / f"{env}.yaml"
if not config_file.exists():
    raise ConfigurationError(...)
with config_file.open(encoding="utf-8") as f:
    config_data = yaml.safe_load(f) or {}
return Settings(**config_data)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_utils/test_config.py -k "env_file_only or missing_file or silent_time" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_utils/test_config.py src/utils/config.py
git commit -m "refactor: load config from single env file"
```

### Task 2: Remove repository references to default.yaml

**Files:**
- Modify: `src/utils/config.py`
- Modify: `docs/PRD.md`
- Modify: `docs/FRAMEWORK_GUIDE.md`
- Modify: `scripts/create_app.sh`
- Test: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write the failing test**

```python
def test_create_app_config_setup_does_not_require_default_yaml(...):
    ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -k "default_yaml" -v`
Expected: FAIL if script/docs/test fixtures still depend on `default.yaml`

**Step 3: Write minimal implementation**

```bash
# update references and generated file handling to dev/prod yaml only
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -v`
Expected: PASS for affected scenarios

**Step 5: Commit**

```bash
git add scripts/create_app.sh tests/test_scripts/test_create_app_sh.py docs/PRD.md docs/FRAMEWORK_GUIDE.md
git commit -m "docs: remove default config references"
```

### Task 3: Validate and close task tracking

**Files:**
- Modify: `docs/task.md`

**Step 1: Run focused validation**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_scripts/test_create_app_sh.py`
Expected: PASS

**Step 2: Run lint**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Update task tracking**

```markdown
- [x] Remove config/default.yaml and load configuration directly from dev.yaml or prod.yaml
```

Recalculate progress totals after checking the item.

**Step 4: Commit**

```bash
git add docs/task.md
git commit -m "chore: update task tracking for config loading change"
```
