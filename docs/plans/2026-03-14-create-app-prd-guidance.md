# Create App PRD Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `scripts/create_app.sh` 성공 메시지의 검토 대상에 `docs/PRD.md`를 추가한다.

**Architecture:** 성공 출력의 "Review and customize" 블록만 최소 수정한다. 회귀 방지를 위해 생성 스크립트 테스트에서 `docs/PRD.md` 안내가 포함되는지 검증한다.

**Tech Stack:** Bash, pytest, uv

---

### Task 1: Track the work

**Files:**
- Modify: `docs/task.md`

`docs/task.md`에 작업을 추가하고 진행률을 갱신한다.

### Task 2: Add failing test

**Files:**
- Modify: `tests/test_scripts/test_create_app_sh.py`

성공 출력에 `docs/PRD.md`가 포함되어야 한다는 기대를 추가하고, `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`로 먼저 실패를 확인한다.

### Task 3: Implement minimal output change

**Files:**
- Modify: `scripts/create_app.sh`

성공 메시지의 검토 목록에 `docs/PRD.md` 한 줄을 추가한다.

### Task 4: Verify and close

**Files:**
- Modify: `docs/task.md`

`uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -q`와 `uv run ruff check .`를 실행한 뒤 작업을 완료 처리한다.
