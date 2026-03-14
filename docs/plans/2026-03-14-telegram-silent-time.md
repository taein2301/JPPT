# Telegram Silent Time Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Telegram silent-time configuration that suppresses all Telegram notifications during the configured window.

**Architecture:** Extend the config schema with an optional silent-time policy under `telegram`, load it at startup with the rest of the settings, and pass it into `TelegramNotifier`. The notifier will decide at send time whether the current local time is inside the blocked window, including overnight ranges, and skip sending without raising.

**Tech Stack:** Python 3.11, Pydantic, PyYAML, Typer, python-telegram-bot, pytest

---

### Task 1: Track the work and define tests

**Files:**
- Modify: `docs/task.md`
- Modify: `tests/test_utils/test_config.py`
- Modify: `tests/test_utils/test_telegram.py`

**Step 1: Write the failing config test**

```python
def test_load_config_with_telegram_silent_time(tmp_path: Path) -> None:
    config = load_config(env="dev", config_dir=tmp_path)
    assert config.telegram.silent_time.start == "23:00"
```

**Step 2: Write the failing notifier tests**

```python
@pytest.mark.asyncio
async def test_telegram_send_message_skipped_during_silent_time() -> None:
    notifier = TelegramNotifier(...)
    assert await notifier.send_message("test") is False
```

**Step 3: Run the narrow tests to verify failure**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_utils/test_telegram.py --no-cov -v`
Expected: FAIL because the config model and notifier do not support silent time yet

### Task 2: Add silent-time support to config and notifier

**Files:**
- Modify: `src/utils/config.py`
- Modify: `src/utils/telegram.py`
- Modify: `src/utils/app_runner.py`
- Modify: `src/utils/batch_runner.py`
- Modify: `config/default.yaml`
- Modify: `config/dev.yaml.example`
- Modify: `config/prod.yaml.example`

**Step 1: Add the config model**

```python
class TelegramSilentTimeConfig(BaseModel):
    enabled: bool = Field(default=False)
    start: str = Field(default="23:00")
    end: str = Field(default="08:00")
    timezone: str = Field(default="Asia/Seoul")
```

**Step 2: Pass the policy into the notifier**

```python
notifier = TelegramNotifier(
    bot_token=settings.telegram.bot_token,
    chat_id=settings.telegram.chat_id,
    enabled=settings.telegram.enabled,
    silent_time=settings.telegram.silent_time,
)
```

**Step 3: Implement the minimal skip logic**

```python
if self._is_silent_time():
    logger.info("Telegram notification skipped due to silent time")
    return False
```

**Step 4: Re-run the narrow tests**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_utils/test_telegram.py --no-cov -v`
Expected: PASS

### Task 3: Validate and close the tracking task

**Files:**
- Modify: `docs/task.md`

**Step 1: Run the relevant validation**

Run: `uv run pytest tests/test_utils/test_config.py tests/test_utils/test_telegram.py --no-cov -v`
Expected: PASS

**Step 2: Run required lint**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Mark the task complete and recalculate progress**

```markdown
- [x] Add Telegram silent time configuration and block notifications during the configured window
```

**Step 4: Commit**

```bash
git add docs/task.md docs/plans/2026-03-14-telegram-silent-time.md \
  tests/test_utils/test_config.py tests/test_utils/test_telegram.py \
  src/utils/config.py src/utils/telegram.py src/utils/app_runner.py \
  src/utils/batch_runner.py config/default.yaml config/dev.yaml.example config/prod.yaml.example
git commit -m "feat: add telegram silent time"
```
