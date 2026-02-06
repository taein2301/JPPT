# JPPT - JKLEE Python 프로젝트 템플릿

모범 사례가 내장된 최신 Python CLI 애플리케이션 템플릿입니다.

## 주요 기능

- 🎯 **Typer CLI**: 깔끔한 명령줄 인터페이스
- ⚙️ **Pydantic Settings**: YAML 계층 구조 기반의 타입 안전 설정 관리
- 📝 **Loguru**: 날짜 기반 로테이션(`_YYYYMMDD.log`) 지원 구조화된 로깅
- 🔄 **Tenacity**: 지수 백오프 기반 재시도 로직
- 📱 **Telegram**: 인터랙티브 설정을 지원하는 내장 알림 기능
- 🌐 **httpx**: 타임아웃 및 에러 핸들링 내장 비동기 HTTP 클라이언트
- 🧪 **pytest**: 80% 커버리지 요구사항
- 🔍 **mypy**: 엄격한 타입 검사
- ✨ **ruff**: 빠른 린팅 및 포매팅

## 빠른 시작

### 새 프로젝트 생성

**Linux/macOS:**
```bash
# 템플릿으로부터 새 프로젝트 생성
./scripts/create_app.sh my-awesome-app

# 옵션과 함께 생성
./scripts/create_app.sh my-app --skip-tests  # 초기 테스트 건너뛰기
./scripts/create_app.sh my-app --no-hooks    # pre-commit 훅 건너뛰기
```

**Windows (PowerShell):**
```powershell
# 템플릿으로부터 새 프로젝트 생성
.\scripts\create_app.ps1 my-awesome-app

# 옵션과 함께 생성
.\scripts\create_app.ps1 my-app -SkipTests   # 초기 테스트 건너뛰기
.\scripts\create_app.ps1 my-app -NoHooks     # pre-commit 훅 건너뛰기
```

이 명령은 다음을 수행합니다:
- ✅ Python 3.11+, uv, GitHub CLI 설치 확인
- ✅ 앱 이름 유효성 검사 (소문자, 숫자, 하이픈, 언더스코어만 허용)
- ✅ 새 프로젝트 디렉토리 생성 (`../my-app`)
- ✅ 빌드 아티팩트 제외하고 템플릿 복사
- ✅ 설정 파일에서 프로젝트 이름 업데이트 (`default.yaml`, `pyproject.toml`)
- ✅ 새 프로젝트용 `README.md` 및 `docs/PRD.md` 생성
- ✅ git 저장소 초기화 및 최초 커밋
- ✅ GitHub 비공개 저장소 생성 및 push
- ✅ 모든 의존성 설치
- ✅ 설정 파일 생성 (`dev.yaml`)
- ✅ **인터랙티브 텔레그램 설정** (API에서 Chat ID 자동 조회)
- ✅ pre-commit 훅 설치 (선택사항)
- ✅ 초기 테스트 실행 (선택사항)

### JPPT 템플릿 자체 개발

JPPT 템플릿 자체를 수정하려면 (새 프로젝트 생성이 아닌 경우):

**Linux/macOS:**
```bash
cd JPPT  # JPPT 디렉토리로 이동
uv sync --all-extras
cp config/dev.yaml.example config/dev.yaml
```

**Windows (PowerShell):**
```powershell
cd JPPT  # JPPT 디렉토리로 이동
uv sync --all-extras
Copy-Item config/dev.yaml.example config/dev.yaml
```

### 애플리케이션 실행

**Linux/macOS:**
```bash
# 빠른 실행 스크립트 (권장)
./run.sh              # 시작 모드, 개발 환경
./run.sh batch        # 배치 모드, 개발 환경
./run.sh start prod   # 시작 모드, 운영 환경
```

**Windows (PowerShell):**
```powershell
# 빠른 실행 스크립트 (권장)
.\run.ps1              # 시작 모드, 개발 환경
.\run.ps1 batch        # 배치 모드, 개발 환경
.\run.ps1 start prod   # 시작 모드, 운영 환경
```

**또는 uv를 직접 사용 (모든 플랫폼):**
```bash
uv run python -m src.main start --env dev
uv run python -m src.main batch --env dev
```

### 개발 명령어

```bash
# 테스트 실행
uv run pytest

# 코드 포맷팅
uv run ruff format .

# 타입 검사
uv run mypy src/

# 모든 pre-commit 검사 실행
uv run pre-commit run --all-files
```

## 프로젝트 구조

```
src/
├── main.py              # CLI 진입점
├── core/                # 비즈니스 로직
└── utils/               # 재사용 가능한 유틸리티
    ├── config.py        # 설정 관리 (Pydantic)
    ├── logger.py        # 로깅 설정 (Loguru)
    ├── app_runner.py    # App 모드 (데몬)
    ├── batch_runner.py  # Batch 모드 (일회성)
    ├── exceptions.py    # 커스텀 예외 계층
    ├── retry.py         # 재시도 데코레이터 (tenacity)
    ├── signals.py       # Graceful Shutdown
    ├── http_client.py   # 비동기 HTTP 클라이언트 (httpx)
    └── telegram.py      # 텔레그램 알림

scripts/                 # 자동화 스크립트
├── create_app.sh        # 프로젝트 생성기 (Linux/macOS)
└── create_app.ps1       # 프로젝트 생성기 (Windows)

run.sh                   # 빠른 실행 래퍼 (Linux/macOS)
run.ps1                  # 빠른 실행 래퍼 (Windows)

tests/                   # 테스트 스위트
config/                  # 설정 파일
docs/                    # 문서
```

## 설정

### 계층형 설정 시스템

설정은 계층적으로 로드되며, 각 계층이 이전 설정을 오버라이드합니다:

1. **`config/default.yaml`** — 기본값 및 스키마 (git에 커밋)
2. **`config/{env}.yaml`** — 환경별 오버라이드 (gitignore)
3. **환경 변수** — 시크릿을 위한 최종 오버라이드

```yaml
# config/default.yaml
app:
  name: "jppt"
  version: "0.1.0"
  debug: false

logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
  rotation: "00:00"       # 매일 자정에 로테이션
  retention: "10 days"    # 10일간 보관

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
```

### 텔레그램 설정

텔레그램은 두 가지 방법으로 설정할 수 있습니다:

**1. 인터랙티브 설정 (권장):** `create_app.sh` 실행 시 스크립트가:
   - Bot Token 입력 요청 ([@BotFather](https://t.me/BotFather)에서 발급)
   - Telegram API에서 사용 가능한 Chat ID를 자동 조회
   - `config/default.yaml`에 설정값 직접 저장

**2. 환경 변수 오버라이드:**
   ```bash
   # Linux/macOS
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```
   ```powershell
   # Windows (PowerShell)
   $env:TELEGRAM_BOT_TOKEN="your-token"
   $env:TELEGRAM_CHAT_ID="your-chat-id"
   ```

### 환경별 설정

```bash
# 개발 환경 (create_app.sh에서 자동 생성)
config/dev.yaml

# 운영 환경 (수동 생성)
cp config/dev.yaml.example config/prod.yaml
# 운영 환경 설정으로 prod.yaml 편집
```

## 로깅

로그는 `logs/` 디렉토리에 날짜 기반 자동 로테이션으로 저장됩니다:

- **현재 로그:** `logs/{app_name}.log` (배치 모드: `{app_name}_batch.log`)
- **로테이션 로그:** `logs/{app_name}_YYYYMMDD.log` (예: `myapp_20260206.log`)
- **로테이션:** 매일 자정 (설정 가능)
- **보관 기간:** 기본 10일 (설정 가능)

## 스크립트

### 프로젝트 생성기 (`scripts/create_app.sh`)

JPPT 템플릿으로부터 새 프로젝트를 생성합니다.

**Linux/macOS:**
```bash
./scripts/create_app.sh <app-name> [OPTIONS]
./scripts/create_app.sh --help    # 옵션 보기
```

**Windows (`scripts/create_app.ps1`):**
```powershell
.\scripts\create_app.ps1 <app-name> [OPTIONS]
.\scripts\create_app.ps1 -Help    # 옵션 보기
```

**옵션:**
| 옵션 | 설명 |
|------|------|
| `--skip-tests` / `-SkipTests` | 초기 테스트 실행 건너뛰기 |
| `--no-hooks` / `-NoHooks` | pre-commit 훅 설치 건너뛰기 |
| `--help` / `-Help` | 사용법 표시 |

**필수 도구:**
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — 패키지 관리자
- [GitHub CLI](https://cli.github.com/) — 저장소 생성 (`gh auth login` 필요)

### 실행 스크립트

빠른 실행 래퍼 — 간편한 앱 실행 도구입니다.

**Linux/macOS (`run.sh`):**
```bash
./run.sh [MODE] [ENV]
./run.sh --help           # 사용법 보기

# 예시:
./run.sh                  # 시작 모드, 개발 환경
./run.sh batch            # 배치 모드, 개발 환경
./run.sh start prod       # 시작 모드, 운영 환경
```

**Windows (`run.ps1`):**
```powershell
.\run.ps1 [MODE] [ENV]
.\run.ps1 -Help           # 사용법 보기

# 예시:
.\run.ps1                 # 시작 모드, 개발 환경
.\run.ps1 batch           # 배치 모드, 개발 환경
.\run.ps1 start prod      # 시작 모드, 운영 환경
```

## 개발

Pre-commit 훅은 `./scripts/create_app.sh`에 의해 자동으로 설치됩니다.

```bash
# 수동으로 훅 설치
uv run pre-commit install

# 모든 검사 실행
uv run pre-commit run --all-files
```

## 라이선스

MIT
