# Create App Success Output Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `scripts/create_app.sh` 성공 메시지에서 잘못된 Telegram 환경변수 안내를 제거하고 `config/dev.yaml` 중심 안내로 정리한다.

**Architecture:** 성공 출력의 "Next steps" 블록만 최소 수정한다. 회귀 방지를 위해 생성 스크립트 테스트에서 성공 출력에 Telegram env var 안내가 없는지 검증한다.

**Tech Stack:** Bash, pytest, uv

---

### Task 1: Track the work

**Files:**
- Modify: `docs/task.md`

**Step 1: Add unchecked task**

`docs/task.md`에 성공 출력 정리 작업을 추가한다.

**Step 2: Recalculate progress**

작업 수와 진행률을 갱신한다.

### Task 2: Add failing test

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write failing test**

성공적으로 생성된 출력에서 다음 문자열이 없어야 함을 검증한다.
- `Set up Telegram (optional):`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

그리고 `config/dev.yaml` 안내는 유지되는지 확인한다.

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`

Expected: 현재 성공 출력에 Telegram env var 안내가 남아 있어 실패한다.

### Task 3: Implement minimal output change

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Rewrite next steps**

Telegram 설정 블록을 제거하고 `config/dev.yaml` 검토 안내로 통합한다.

**Step 2: Keep numbering clear**

번호를 다시 정리해 출력 가독성을 유지한다.

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

검증 후 `docs/task.md`를 완료 상태로 갱신한다.
