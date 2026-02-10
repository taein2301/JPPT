# 로그 경로를 $HOME/logs로 변경 구현 계획

> **Status:** ✅ **COMPLETED** (2026-02-10)
> **Commits:** 124b00d, b742c3b, 8c9aceb, a4b8753

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 애플리케이션 로그 파일을 프로젝트 디렉토리(`PROJECT_ROOT/logs`)에서 홈 디렉토리(`$HOME/logs`)로 변경

**Architecture:** `main.py`에서 `setup_logger` 호출 시 명시적으로 전달하는 log_file 경로를 `Path.home() / "logs"`로 변경. `logger.py`는 이미 기본값으로 `$HOME/logs`를 사용하고 있으나, `main.py`가 프로젝트 루트 경로를 명시적으로 전달하여 기본값이 사용되지 않는 상황.

**Tech Stack:** Python 3.11+, Typer, Loguru, pytest

**Why this change:**
- 로그 파일을 사용자 홈 디렉토리에 보관하여 프로젝트 디렉토리를 깔끔하게 유지
- 여러 프로젝트의 로그를 중앙 집중화된 위치에서 관리
- `logger.py`의 기본값과 일관성 유지

---

## Task 1: 로그 경로 변경 테스트 작성

**Files:**
- Modify: `tests/test_main.py:137-162`

**Step 1: 실패하는 테스트 작성**

`tests/test_main.py`의 `test_log_file_path_is_in_project_root` 함수를 수정하여 `$HOME/logs` 경로를 검증하도록 변경:

```python
@patch("src.main.setup_logger")
@patch("src.main.load_config")
def test_log_file_path_is_in_home_directory(
    mock_load_config: AsyncMock,
    mock_setup_logger: AsyncMock,
    mock_asyncio_run: AsyncMock,
) -> None:
    """Test that log file path is in user's home directory ($HOME/logs)."""
    from pathlib import Path
    from src.utils.config import Settings

    mock_load_config.return_value = Settings(
        app={"name": "test-app", "version": "0.1.0", "debug": True},
        logging={"level": "INFO"},
        telegram={"enabled": False},
    )

    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0

    # Verify setup_logger was called with path to $HOME/logs
    call_kwargs = mock_setup_logger.call_args[1]
    log_file = call_kwargs["log_file"]

    # Log file should be: $HOME / "logs" / "test-app.log"
    home_logs = Path.home() / "logs"
    assert log_file.is_absolute(), f"Log file path should be absolute, got: {log_file}"
    assert log_file.parent == home_logs, f"Log file should be in $HOME/logs, got: {log_file.parent}"
    assert log_file.name == "test-app.log"
```

**Step 2: 테스트 실행하여 실패 확인**

Run: `uv run pytest tests/test_main.py::test_log_file_path_is_in_home_directory -v`

Expected: FAIL - 현재 코드는 `PROJECT_ROOT/logs`를 사용하므로 assertion 실패

**Step 3: 커밋**

```bash
git add tests/test_main.py
git commit -m "test: add test for $HOME/logs path verification"
```

---

## Task 2: main.py의 로그 경로 변경

**Files:**
- Modify: `src/main.py:73-76` (start 명령)
- Modify: `src/main.py:115-118` (batch 명령)

**Step 1: start 명령의 로그 경로 변경**

`src/main.py`의 `start` 함수에서 log_file 경로를 수정:

```python
# Before (line 73):
log_file = PROJECT_ROOT / "logs" / f"{settings.app.name}.log"

# After:
log_file = Path.home() / "logs" / f"{settings.app.name}.log"
```

**Step 2: batch 명령의 로그 경로 변경**

`src/main.py`의 `batch` 함수에서 log_file 경로를 수정:

```python
# Before (line 115):
log_file = PROJECT_ROOT / "logs" / f"{settings.app.name}_batch.log"

# After:
log_file = Path.home() / "logs" / f"{settings.app.name}_batch.log"
```

**Step 3: 테스트 실행하여 통과 확인**

Run: `uv run pytest tests/test_main.py::test_log_file_path_is_in_home_directory -v`

Expected: PASS - 이제 `$HOME/logs` 경로를 사용

**Step 4: 전체 테스트 실행**

Run: `uv run pytest tests/test_main.py -v`

Expected: 모든 테스트 PASS (다른 테스트는 영향 받지 않음)

**Step 5: 커밋**

```bash
git add src/main.py
git commit -m "refactor: change log path from PROJECT_ROOT to HOME directory

- start command: use Path.home() / 'logs' instead of PROJECT_ROOT / 'logs'
- batch command: use Path.home() / 'logs' instead of PROJECT_ROOT / 'logs'
- Aligns with logger.py default behavior
- Keeps project directory clean"
```

---

## Task 3: 통합 테스트 실행

**Files:**
- Test: `tests/test_main.py`
- Test: `tests/test_utils/test_logger.py`

**Step 1: 전체 테스트 스위트 실행**

Run: `uv run pytest`

Expected: 모든 테스트 PASS, 커버리지 80% 이상

**Step 2: 실제 실행 테스트**

애플리케이션을 실제로 실행하여 로그 파일이 올바른 위치에 생성되는지 확인:

```bash
# dev 환경 실행 (백그라운드)
uv run python -m src.main start --env dev &
APP_PID=$!

# 잠시 대기 (로그 파일 생성 시간)
sleep 2

# 로그 파일 확인
ls -la ~/logs/

# 프로세스 종료
kill $APP_PID
```

Expected: `~/logs/jppt.log` 파일이 생성되어 있어야 함

**Step 3: 로그 파일 내용 확인**

```bash
cat ~/logs/jppt.log
```

Expected: "Logger initialized", "Starting jppt in app mode" 등의 로그 메시지 확인

**Step 4: 정리**

로그 파일이 정상적으로 생성되었으면 테스트 로그 제거:

```bash
rm -f ~/logs/jppt.log ~/logs/jppt_*.log
```

---

## Task 4: 문서 업데이트 (선택사항)

**Files:**
- Modify: `CLAUDE.md` (if mentions log path)
- Modify: `README.md` (if mentions log path)
- Modify: `docs/FRAMEWORK_GUIDE.md` (if mentions log path)

**Step 1: 문서에서 로그 경로 언급 확인**

```bash
grep -r "PROJECT_ROOT.*logs" docs/ README.md CLAUDE.md 2>/dev/null || echo "No mentions found"
```

**Step 2: 필요시 문서 업데이트**

문서에 로그 경로가 언급되어 있다면:
- `PROJECT_ROOT/logs` → `$HOME/logs` 또는 `~/logs`로 변경
- "로그 파일은 홈 디렉토리의 logs 폴더에 저장됩니다" 설명 추가

**Step 3: 변경사항 커밋**

```bash
git add docs/ README.md CLAUDE.md
git commit -m "docs: update log path location to $HOME/logs"
```

---

## Task 5: 최종 검증 및 정리

**Files:**
- All modified files

**Step 1: 최종 테스트 실행**

```bash
# 전체 테스트 스위트
uv run pytest

# 린트 체크
uv run ruff check src tests

# 포맷 체크
uv run ruff format --check src tests
```

Expected: 모든 검사 통과

**Step 2: 변경사항 요약 검토**

```bash
git log --oneline -5
git diff origin/main..HEAD
```

**Step 3: 최종 확인**

변경된 파일 목록:
- `src/main.py`: 로그 경로 변경
- `tests/test_main.py`: 테스트 업데이트
- `docs/`: 문서 업데이트 (필요시)

**Step 4: PR 준비 (선택사항)**

브랜치에서 작업했다면:
```bash
git push origin <branch-name>
gh pr create --title "refactor: change log path to HOME directory" --body "$(cat <<'EOF'
## Summary
- Change log file location from PROJECT_ROOT/logs to $HOME/logs
- Update tests to verify new path
- Update documentation

## Test Plan
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing confirms logs created in $HOME/logs

## Rationale
- Keeps project directory clean
- Centralizes logs in user home directory
- Aligns with logger.py default behavior

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Summary

**변경 사항:**
1. `src/main.py`: 로그 경로를 `Path.home() / "logs"`로 변경
2. `tests/test_main.py`: 테스트를 `$HOME/logs` 검증으로 업데이트
3. 문서 업데이트 (필요시)

**테스트 전략:**
- TDD: 먼저 실패하는 테스트 작성
- 코드 변경 후 테스트 통과 확인
- 전체 테스트 스위트 실행
- 실제 실행으로 동작 확인

**예상 소요 시간:** 15-20분

**Prerequisites:**
- uv 설치 및 환경 설정 완료
- 테스트 환경 정상 작동

**Risks:**
- 기존에 `PROJECT_ROOT/logs`에 있던 로그 파일은 자동으로 마이그레이션되지 않음
- 사용자가 직접 필요한 로그 파일을 `$HOME/logs`로 이동해야 함
