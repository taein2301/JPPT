# Create App Readme/Task Exclusion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `scripts/create_app.sh`로 생성한 프로젝트에서 `README.ko.md`와 `docs/task.md`가 포함되지 않도록 변경한다.

**Architecture:** 템플릿 복사 단계의 `rsync` 제외 목록을 최소 수정해서 생성 결과를 제어한다. 회귀 방지를 위해 생성 스크립트 테스트에 두 파일의 부재와 `README.md` 유지 여부를 추가한다.

**Tech Stack:** Bash, pytest, uv

---

### Task 1: Track the new generator behavior

**Files:**
- Modify: `docs/task.md`

**Step 1: Add the unchecked task**

`docs/task.md`에 생성 프로젝트에서 `README.ko.md`와 `docs/task.md`를 제외하는 작업을 추가한다.

**Step 2: Recalculate progress**

총 작업 수와 완료율을 실제 체크리스트 상태에 맞게 갱신한다.

### Task 2: Add the failing generator test

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write the failing test**

기존 생성 스크립트 성공 테스트에 생성 결과 기준으로 다음을 검증한다.
- `README.md`는 존재한다.
- `README.ko.md`는 존재하지 않는다.
- `docs/task.md`는 존재하지 않는다.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -q`

Expected: 생성 결과에 `README.ko.md` 또는 `docs/task.md`가 남아 있어 실패한다.

### Task 3: Implement the minimal generator change

**Files:**
- Modify: `scripts/create_app.sh`

**Step 1: Write minimal implementation**

`copy_template()`의 `rsync` 제외 목록에 `README.ko.md`와 `docs/task.md`를 추가한다.

**Step 2: Keep the change minimal**

복사 후 삭제 로직은 추가하지 않고 제외 목록만 조정한다.

### Task 4: Verify and close the task

**Files:**
- Modify: `docs/task.md`

**Step 1: Run targeted tests**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py -q`

Expected: PASS

**Step 2: Run required lint**

Run: `uv run ruff check scripts/create_app.sh tests/test_scripts/test_create_app_sh.py docs/task.md`

Expected: PASS if the repo accepts those paths, otherwise run `uv run ruff check .`

**Step 3: Mark the task complete**

검증과 lint가 통과하면 `docs/task.md`에서 해당 작업을 체크하고 진행률을 다시 계산한다.
