"""Tests for the create_app.sh project generator."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def test_create_app_copies_generated_agents_template(tmp_path: Path) -> None:
    """create_app.sh should generate a root AGENTS.md for new projects."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    project_dir = tmp_path / "sample-app"
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.0.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'Logged in to github.com'\n"
        "  echo 'Token scopes: repo'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "README.md").exists()
    assert not (project_dir / "README.ko.md").exists()
    assert not (project_dir / "docs" / "task.md").exists()
    assert not (project_dir / "config" / "default.yaml").exists()
    dev_config = (project_dir / "config" / "dev.yaml").read_text(encoding="utf-8")
    prod_example = (project_dir / "config" / "prod.yaml.example").read_text(encoding="utf-8")
    assert 'name: "sample-app"' in dev_config
    assert 'name: "sample-app"' in prod_example
    agents_content = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "JPPT" in agents_content
    assert "원본 파일은 수정 불가" in agents_content
    assert "src/utils/" in agents_content
    assert "신규 생성" in agents_content
    assert "삭제" in agents_content
    assert "Set up Telegram (optional):" not in result.stdout
    assert "TELEGRAM_BOT_TOKEN" not in result.stdout
    assert "TELEGRAM_CHAT_ID" not in result.stdout
    review_block = result.stdout.split("  2. Review and customize:", 1)[1]
    assert "config/dev.yaml" in review_block
    assert "docs/PRD.md" in review_block


def test_create_app_accepts_repo_scope_from_github_api_headers(tmp_path: Path) -> None:
    """create_app.sh should detect repo scope from GitHub API headers."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.0.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'Logged in to github.com'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"-i\" ] && [ \"$3\" = \"user\" ]; then\n"
        "  printf 'HTTP/1.1 200 OK\\r\\nX-OAuth-Scopes: gist, repo, read:org\\r\\n\\r\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout


def test_create_app_does_not_fail_when_gh_hides_scope_metadata(tmp_path: Path) -> None:
    """create_app.sh should continue when gh omits token scope metadata."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.87.3'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'github.com'\n"
        "  echo '  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)'\n"
        "  echo '  - Active account: true'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"-i\" ] && [ \"$3\" = \"user\" ]; then\n"
        "  printf 'HTTP/2 200 OK\\r\\n'"
        "'Access-Control-Expose-Headers: X-OAuth-Scopes\\r\\n\\r\\n{}'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout


def test_create_app_creates_dev_config_and_sends_telegram_sample(tmp_path: Path) -> None:
    """create_app.sh should create dev config and send a Telegram sample message."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    project_dir = tmp_path / "sample-app"
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    curl_log = tmp_path / "curl.log"

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.87.3'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'github.com'\n"
        "  echo '  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)'\n"
        "  echo '  - Active account: true'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "curl",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "log_path = Path(os.environ['TEST_CURL_LOG'])\n"
        "args = sys.argv[1:]\n"
        "log_path.write_text('ARGS=' + ' '.join(args) + '\\n', encoding='utf-8')\n"
        "if any('getUpdates' in arg for arg in args):\n"
        "    sys.stdout.write("
        '\"{\\"ok\\":true,\\"result\\":[{\\"message\\":{\\"chat\\":{\\"id\\":123456,\\"first_name\\":\\"Sample\\",\\"username\\":\\"sample\\"}}}]}\"'
        ")\n"
        "    raise SystemExit(0)\n"
        "if any('sendMessage' in arg for arg in args):\n"
        "    sys.stdout.write('{\"ok\":true}')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(1)\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"
    env["TEST_CURL_LOG"] = str(curl_log)

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="test-bot-token\n123456\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (project_dir / "config" / "dev.yaml").exists()
    curl_args = curl_log.read_text(encoding="utf-8")
    assert "sendMessage" in curl_args
    assert "sample-app create 성공" in curl_args


def test_create_app_accepts_spaced_telegram_success_response(tmp_path: Path) -> None:
    """create_app.sh should treat spaced Telegram JSON success as successful."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.87.3'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'github.com'\n"
        "  echo '  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)'\n"
        "  echo '  - Active account: true'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "curl",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import sys\n"
        "\n"
        "args = sys.argv[1:]\n"
        "if any('getUpdates' in arg for arg in args):\n"
        "    sys.stdout.write("
        "'{\"ok\": true, \"result\": [{\"message\": {\"chat\": {\"id\": 123456}}}]}'"
        ")\n"
        "    raise SystemExit(0)\n"
        "if any('sendMessage' in arg for arg in args):\n"
        "    sys.stdout.write('{\"ok\": true, \"result\": {\"message_id\": 1}}')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(1)\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="test-bot-token\n123456\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Telegram sample message sent" in result.stdout


def test_create_app_accepts_enter_for_existing_directory_prompt(tmp_path: Path) -> None:
    """Pressing Enter should accept deleting an existing target directory."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    project_dir = tmp_path / "sample-app"
    project_dir.mkdir()
    (project_dir / "old.txt").write_text("legacy", encoding="utf-8")
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.87.3'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'github.com'\n"
        "  echo '  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)'\n"
        "  echo '  - Active account: true'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (project_dir / "README.md").exists()
    assert not (project_dir / "old.txt").exists()


def test_create_app_accepts_enter_for_existing_repo_prompt(tmp_path: Path) -> None:
    """Pressing Enter should accept deleting an existing GitHub repository."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    gh_log = tmp_path / "gh.log"

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ] || [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "log_path = Path(os.environ['TEST_GH_LOG'])\n"
        "args = sys.argv[1:]\n"
        "existing = log_path.read_text(encoding='utf-8') if log_path.exists() else ''\n"
        "log_path.write_text(existing + ' '.join(args) + '\\n', encoding='utf-8')\n"
        "if args[:1] == ['--version']:\n"
        "    print('gh version 2.87.3')\n"
        "    raise SystemExit(0)\n"
        "if args[:2] == ['auth', 'status']:\n"
        "    print('github.com')\n"
        "    print('  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)')\n"
        "    print('  - Active account: true')\n"
        "    raise SystemExit(0)\n"
        "if args[:2] == ['api', 'user']:\n"
        "    print('stub-user')\n"
        "    raise SystemExit(0)\n"
        "if args[:3] == ['repo', 'view', 'stub-user/sample-app']:\n"
        "    raise SystemExit(0)\n"
        "if args[:4] == ['repo', 'delete', 'stub-user/sample-app', '--yes']:\n"
        "    raise SystemExit(0)\n"
        "if args[:2] == ['repo', 'create']:\n"
        "    raise SystemExit(0)\n"
        "if args[:3] == ['repo', 'view', '--json']:\n"
        "    print('https://github.com/stub-user/sample-app')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(0)\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"
    env["TEST_GH_LOG"] = str(gh_log)

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    gh_calls = gh_log.read_text(encoding="utf-8")
    assert "repo delete stub-user/sample-app --yes" in gh_calls


def test_create_app_creates_dev_config_before_dependency_install(tmp_path: Path) -> None:
    """config/dev.yaml should exist even if dependency installation fails."""
    source_repo = Path(__file__).resolve().parents[2]
    repo_root = tmp_path / "JPPT"
    shutil.copytree(
        source_repo,
        repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
        ),
    )
    project_dir = tmp_path / "sample-app"
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    _write_executable(
        fakebin / "python3",
        "#!/usr/bin/env bash\n"
        "echo 'Python 3.11.9'\n",
    )
    _write_executable(
        fakebin / "uv",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'uv 0.7.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"sync\" ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"run\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "gh",
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'gh version 2.87.3'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'github.com'\n"
        "  echo '  ✓ Logged in to github.com account stub-user (GITHUB_TOKEN)'\n"
        "  echo '  - Active account: true'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"api\" ] && [ \"$2\" = \"user\" ]; then\n"
        "  echo 'stub-user'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] \\\n"
        "  && [ \"$3\" = 'stub-user/sample-app' ]; then\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"create\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  echo 'https://github.com/stub-user/sample-app'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        fakebin / "git",
        "#!/usr/bin/env bash\n"
        "case \"$1\" in\n"
        "  init)\n"
        "    mkdir -p .git\n"
        "    exit 0\n"
        "    ;;\n"
        "  add|commit)\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fakebin / "rsync",
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import shutil\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "args = sys.argv[1:]\n"
        "src = Path(args[-2]).resolve()\n"
        "dst = Path(args[-1]).resolve()\n"
        "exclude_names = set()\n"
        "exclude_paths = set()\n"
        "for arg in args[:-2]:\n"
        "    if not arg.startswith('--exclude='):\n"
        "        continue\n"
        "    pattern = arg.split('=', 1)[1]\n"
        "    if pattern.endswith('/'):\n"
        "        exclude_names.add(pattern.rstrip('/'))\n"
        "    else:\n"
        "        exclude_paths.add(pattern)\n"
        "for item in src.rglob('*'):\n"
        "    rel = item.relative_to(src)\n"
        "    rel_str = rel.as_posix()\n"
        "    if any(part in exclude_names for part in rel.parts):\n"
        "        continue\n"
        "    if rel_str in exclude_paths or rel.name.endswith('.pyc'):\n"
        "        continue\n"
        "    target = dst / rel\n"
        "    if item.is_dir():\n"
        "        target.mkdir(parents=True, exist_ok=True)\n"
        "    else:\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        shutil.copy2(item, target)\n"
        "sys.exit(0)\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env['PATH']}"
    env["SHELL"] = shutil.which("true") or "/usr/bin/true"

    result = subprocess.run(
        ["bash", "scripts/create_app.sh", "sample-app", "--skip-tests", "--no-hooks"],
        cwd=repo_root,
        env=env,
        input="\n",
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode != 0
    assert (project_dir / "config" / "dev.yaml").exists()
