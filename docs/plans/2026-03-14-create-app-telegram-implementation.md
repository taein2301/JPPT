# create_app Telegram setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure `scripts/create_app.sh` creates `config/dev.yaml` for generated projects and sends one Telegram sample message with the app name after Telegram setup completes.

**Architecture:** Reuse the existing `setup_config` copy step for `config/dev.yaml` creation and keep the Telegram change localized to `setup_telegram_optional`. Add a narrow integration-style shell-script test with stubbed executables and stubbed `curl` calls to verify both the config file creation and the outgoing Telegram sample message.

**Tech Stack:** Bash, pytest, subprocess stubs

---

### Task 1: Add failing shell-script test

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`
- Test: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write the failing test**

Add a test that runs `scripts/create_app.sh` with:
- stubbed `curl` returning a successful `getUpdates` payload and capturing a `sendMessage` request
- stdin that provides a bot token and chat id
- assertions that generated project contains `config/dev.yaml`
- assertions that the captured Telegram send request contains `<app-name> create 성공`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -k telegram --no-cov -v`
Expected: FAIL because the current script does not send the sample message and may not prove `config/dev.yaml` creation in that path

**Step 3: Write minimal implementation**

Modify `scripts/create_app.sh` to:
- pass the app name into Telegram setup
- send one `sendMessage` request after saving Telegram config

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -k telegram --no-cov -v`
Expected: PASS

### Task 2: Verify full changed-area behavior

**Files:**
- Modify: `scripts/create_app.sh`
- Modify: `docs/task.md`

**Step 1: Run full changed-area test file**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -v`
Expected: PASS

**Step 2: Run lint**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Update task tracking**

- Mark the new task complete in `docs/task.md`
- Recalculate progress numbers

**Step 4: Commit**

```bash
git add scripts/create_app.sh tests/test_scripts/test_create_app_sh.py docs/task.md docs/plans/2026-03-14-create-app-telegram-design.md docs/plans/2026-03-14-create-app-telegram-implementation.md
git commit -m "feat: send create-app telegram sample message"
```
