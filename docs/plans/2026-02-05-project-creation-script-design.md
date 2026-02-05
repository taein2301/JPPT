# 프로젝트 생성 스크립트 설계

## 개요

JPPT 템플릿으로부터 새 프로젝트를 자동 생성하는 스크립트로 `create_app.sh`/`create_app.ps1` 재설계.

## 목표

- 앱 이름을 파라미터로 받아 새 프로젝트 생성
- JPPT 상위 디렉토리에 프로젝트 복사
- 프로젝트 이름 자동 치환
- GitHub private repository 자동 생성 및 push
- 개발 환경 설정 자동화

## 사용 방법

```bash
# Linux/macOS
./scripts/create_app.sh <app-name> [OPTIONS]
./scripts/create_app.sh my-awesome-app
./scripts/create_app.sh my-app --skip-tests --no-hooks

# Windows
.\scripts\create_app.ps1 <app-name> [OPTIONS]
.\scripts\create_app.ps1 my-awesome-app
.\scripts\create_app.ps1 my-app -SkipTests -NoHooks
```

## 디렉토리 구조

```
Source/
├── JPPT/              (템플릿 원본, 여기서 스크립트 실행)
└── my-app/            (생성된 프로젝트)
    ├── src/
    ├── tests/
    ├── config/
    └── ...
```

## 주요 단계

### 1. 검증 단계

**필수 도구 검증:**
- Python 3.11+
- uv
- gh (GitHub CLI)
- gh auth status (인증 확인)

**앱 이름 검증:**
- 필수 입력
- 영문 소문자, 숫자, 하이픈, 언더스코어만 허용
- 하이픈/언더스코어로 시작 불가
- 정규식: `^[a-z0-9][a-z0-9_-]*$`

**대상 디렉토리 검증:**
- 경로: `$(dirname $JPPT_DIR)/<app-name>`
- 이미 존재하면 에러 발생 후 종료

### 2. 복사 단계

**rsync를 활용한 템플릿 복사:**
```bash
rsync -av \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='.ruff_cache' \
    --exclude='logs/' \
    --exclude='config/dev.yaml' \
    --exclude='config/prod.yaml' \
    "$SOURCE_DIR/" "$TARGET_DIR/"
```

### 3. Git 초기화

```bash
cd "$TARGET_DIR"
git init
git add .
git commit -m "Initial commit from JPPT template"
```

### 4. 프로젝트 이름 치환

**자동 치환 대상:**
1. `config/default.yaml`: `app.name: "my-app"` → `app.name: "my-awesome-app"`
2. `pyproject.toml`: `name = "jppt"` → `name = "my-awesome-app"`
3. `README.md`: 최소 템플릿으로 교체

**README.md 템플릿:**
```markdown
# my-awesome-app

Created from [JPPT](https://github.com/taein2301/JPPT) template.

## Setup

\`\`\`bash
./scripts/create_app.sh
\`\`\`

## Run

\`\`\`bash
./scripts/run.sh              # Start mode (dev)
./scripts/run.sh batch        # Batch mode (dev)
\`\`\`

## Development

\`\`\`bash
uv run pytest                 # Run tests
uv run ruff format .          # Format code
uv run mypy src/              # Type check
\`\`\`
```

### 5. GitHub Repository 생성

```bash
gh repo create "$APP_NAME" \
    --private \
    --source=. \
    --description="Created from JPPT template" \
    --push
```

**실행 흐름:**
1. GitHub에 private repo 생성
2. 로컬 git에 remote origin 자동 설정
3. main 브랜치로 초기 커밋 push
4. Repository URL 반환

### 6. 프로젝트 설정

새 프로젝트 디렉토리에서 실행:
1. `uv sync --all-extras` - 의존성 설치
2. `cp config/dev.yaml.example config/dev.yaml` - Config 파일 생성
3. `mkdir -p logs` - 디렉토리 생성
4. `uv run pre-commit install` - Pre-commit hooks 설치 (옵션)
5. `uv run pytest -v` - 테스트 실행 (옵션)

## 에러 처리

**트랜잭션 방식:**
```bash
cleanup_on_error() {
    if [ -d "$TARGET_DIR" ]; then
        print_warning "Cleaning up incomplete project..."
        rm -rf "$TARGET_DIR"
    fi
}

trap cleanup_on_error ERR
```

**단계별 에러 처리:**
- 검증 실패 → 즉시 종료 (롤백 불필요)
- 복사 실패 → 대상 디렉토리 삭제
- Git 초기화 실패 → 대상 디렉토리 삭제
- GitHub 생성 실패 → 로컬은 유지, 수동 생성 안내
- 의존성 설치 실패 → 프로젝트는 유지, 수동 설치 안내

## 성공 메시지

```
╔════════════════════════════════════════════════╗
║  Project Created Successfully! 🎉              ║
╚════════════════════════════════════════════════╝

Project: my-app
Location: /Users/jklee/Source/my-app
GitHub: https://github.com/taein2301/my-app

Next steps:

  1. Navigate to your project:
     cd ../my-app

  2. Set up environment variables (if needed):
     export TELEGRAM_BOT_TOKEN="your-token"
     export TELEGRAM_CHAT_ID="your-chat-id"

  3. Review and customize:
     config/dev.yaml
     README.md

  4. Start developing:
     ./scripts/run.sh              # Start mode (dev)
     ./scripts/run.sh batch        # Batch mode (dev)
```

## 코드 구조

**함수 분리:**
```bash
# 검증 함수
check_python()
check_uv()
check_gh()
validate_app_name()
check_target_directory()

# 실행 함수
copy_template()
init_git()
substitute_project_name()
create_github_repo()
install_deps()
setup_config()
setup_dirs()
install_hooks()
run_tests_optional()

# 메인 함수
main()
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `--skip-tests` | 초기 테스트 실행 생략 |
| `--no-hooks` | pre-commit hooks 설치 생략 |
| `--help` | 도움말 출력 |

## 제약사항

- GitHub CLI (`gh`) 필수 설치 및 인증 필요
- 대상 디렉토리가 이미 존재하면 실패 (덮어쓰기 불가)
- 앱 이름은 소문자, 숫자, 하이픈, 언더스코어만 허용
