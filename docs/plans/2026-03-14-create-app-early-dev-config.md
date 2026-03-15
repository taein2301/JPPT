# Create App Early Dev Config Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `scripts/create_app.sh`가 의존성 설치 전에 `config/dev.yaml`을 생성하도록 변경한다.

**Architecture:** 템플릿 복사 직후 생성 프로젝트 디렉터리에서 `setup_config()`를 먼저 실행해 `config/dev.yaml`을 만든다. 이후 후반부 `setup_config()`는 기존대로 두거나 제거할 수 있지만, 최소 변경을 위해 기존 idempotent 동작을 유지한다.

**Tech Stack:** Bash, pytest, uv

---

### Task 1: Track the work

**Files:**
- Modify: `docs/task.md`

**Step 1: Add unchecked task**

`docs/task.md`에 `dev.yaml` 조기 생성 작업을 추가한다.

**Step 2: Recalculate progress**

총 작업 수, 완료 수, 진행률을 갱신한다.

### Task 2: Add failing test

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write the failing test**

`uv sync --all-extras`가 실패해도 이미 생성 프로젝트에 `config/dev.yaml`이 존재하는지 검증한다.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`

Expected: 현재는 `setup_config()`가 의존성 설치 후에 호출되어 `config/dev.yaml`이 없어서 실패한다.

### Task 3: Implement minimal change

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Move config creation earlier**

`copy_template()`와 `copy_generated_agents()` 이후, `init_git()` 전에 생성 프로젝트 디렉터리에서 `setup_config()`를 실행한다.

**Step 2: Keep the diff small**

후반부 `setup_config()`는 재호출돼도 안전하므로 제거하지 않는다.

### Task 4: Verify and close

**Files:**
- Modify: `docs/task.md`

**Step 1: Run targeted tests**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`

Expected: PASS

**Step 2: Run lint**

Run: `uv run ruff check .`

Expected: PASS

**Step 3: Mark task complete**

검증이 끝나면 `docs/task.md`를 완료 상태로 갱신한다.
