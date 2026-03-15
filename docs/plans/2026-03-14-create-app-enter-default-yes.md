# Create App Enter Default Yes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `scripts/create_app.sh`의 확인 프롬프트에서 엔터 입력을 기본 `yes`로 처리한다.

**Architecture:** 기존 디렉터리 삭제와 기존 GitHub 저장소 삭제 프롬프트의 조건식만 최소 수정한다. 회귀 방지를 위해 생성 스크립트 테스트에 엔터 입력만으로 계속 진행되는 케이스를 추가한다.

**Tech Stack:** Bash, pytest, uv

---

### Task 1: Track the work

**Files:**
- Modify: `docs/task.md`

**Step 1: Add unchecked task**

`docs/task.md`에 엔터 기본 승인 동작 변경 작업을 추가한다.

**Step 2: Recalculate progress**

총 작업 수, 완료 수, 진행률을 실제 상태로 갱신한다.

### Task 2: Add failing tests

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write failing tests**

다음 두 케이스를 추가한다.
- 기존 대상 디렉터리가 있을 때 입력이 `\n`만 들어오면 삭제 후 계속 진행한다.
- 기존 GitHub 저장소가 있을 때 입력이 `\n`만 들어오면 저장소 삭제 후 계속 진행한다.

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`

Expected: 현재는 엔터가 `No`로 취급되어 실패한다.

### Task 3: Implement the minimal behavior change

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Update prompts**

두 확인 프롬프트를 `[Y/n]`로 바꾸고, 빈 입력 또는 `y/Y`를 승인으로 처리한다.

**Step 2: Keep diff minimal**

공통 헬퍼는 만들지 않고 조건식만 수정한다.

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

검증이 끝나면 `docs/task.md`를 체크 완료로 갱신하고 진행률을 재계산한다.
