# Generated AGENTS Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a generated-project `AGENTS.md` template under `docs/` and make `scripts/create_app.sh` copy it into newly created projects.

**Architecture:** Keep a dedicated template file in `docs/` for generated projects, then add a small copy step in `create_app.sh` after the base template copy. Verify behavior with a narrow pytest integration test that runs the shell script with stubbed external commands.

**Tech Stack:** Bash, pytest, Python stdlib subprocess/pathlib

---

### Task 1: Add tracking and failing generator test

**Files:**
- Modify: `docs/task.md`
- Create: `tests/test_scripts/test_create_app_sh.py`

**Step 1: Write the failing test**

```python
def test_create_app_copies_generated_agents_template(...):
    result = subprocess.run([...])
    assert (generated_dir / "AGENTS.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -v`
Expected: FAIL because `create_app.sh` does not copy generated `AGENTS.md` yet

### Task 2: Add generated AGENTS template and copy step

**Files:**
- Create: `docs/AGENTS.md.sample`
- Modify: `scripts/create_app.sh`

**Step 1: Add the sample file**

```md
# AGENTS.md
- JPPT가 제공한 원본 파일 수정 금지
- src/utils/ 신규 파일 생성 금지
- src/utils/ 파일 삭제 금지
```

**Step 2: Add the copy helper**

```bash
copy_generated_agents() {
    cp "$source_dir/docs/AGENTS.md.sample" "$target_dir/AGENTS.md"
}
```

**Step 3: Re-run the narrow test**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -v`
Expected: PASS

### Task 3: Validate and update tracking

**Files:**
- Modify: `docs/task.md`

**Step 1: Run relevant tests**

Run: `uv run pytest tests/test_scripts/test_create_app_sh.py --no-cov -v`
Expected: PASS

**Step 2: Run required lint**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Mark task complete**

```md
- [x] Add generated-project AGENTS.md template and copy it during create_app.sh project creation
```
