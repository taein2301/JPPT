# JPPT - JKLEE Python 프로젝트 템플릿

모범 사례가 내장된 최신 Python CLI 애플리케이션 템플릿입니다.

## 주요 기능

- 🎯 **Typer CLI**: 깔끔한 명령줄 인터페이스
- ⚙️ **Pydantic Settings**: 타입 안전 설정 관리
- 📝 **Loguru**: 로테이션 기능이 있는 구조화된 로깅
- 🔄 **Tenacity**: 복원력 있는 작업을 위한 재시도 로직
- 📱 **Telegram**: 내장된 알림 기능
- 🧪 **pytest**: 80% 커버리지 요구사항
- 🔍 **mypy**: 엄격한 타입 검사
- ✨ **ruff**: 빠른 린팅 및 포매팅

## 빠른 시작

### 1. 초기 설정

**Linux/macOS:**
```bash
# 원커맨드 설정 (권장)
./scripts/create_app.sh

# 옵션과 함께 설정
./scripts/create_app.sh --skip-tests  # 초기 테스트 건너뛰기
./scripts/create_app.sh --no-hooks    # pre-commit 훅 건너뛰기
```

**Windows (PowerShell):**
```powershell
# 원커맨드 설정 (권장)
.\scripts\create_app.ps1

# 옵션과 함께 설정
.\scripts\create_app.ps1 -SkipTests   # 초기 테스트 건너뛰기
.\scripts\create_app.ps1 -NoHooks     # pre-commit 훅 건너뛰기
```

이 명령은 다음을 수행합니다:
- ✅ Python 3.11+ 및 uv 설치 확인
- ✅ 모든 의존성 설치
- ✅ 설정 파일 생성
- ✅ 로깅 디렉토리 설정
- ✅ pre-commit 훅 설치
- ✅ 초기 테스트 실행 (선택사항)

### 2. 애플리케이션 실행

**Linux/macOS:**
```bash
# 빠른 실행 스크립트 (권장)
./scripts/run.sh              # 시작 모드, 개발 환경
./scripts/run.sh batch        # 배치 모드, 개발 환경
./scripts/run.sh start prod   # 시작 모드, 운영 환경
```

**Windows (PowerShell):**
```powershell
# 빠른 실행 스크립트 (권장)
.\scripts\run.ps1              # 시작 모드, 개발 환경
.\scripts\run.ps1 batch        # 배치 모드, 개발 환경
.\scripts\run.ps1 start prod   # 시작 모드, 운영 환경
```

**또는 uv를 직접 사용 (모든 플랫폼):**
```bash
uv run python -m src.main start --env dev
uv run python -m src.main batch --env dev
```

### 3. 개발 명령어

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
    ├── config.py
    ├── logger.py
    ├── app_runner.py
    ├── batch_runner.py
    └── ...

scripts/                 # 자동화 스크립트
├── create_app.sh        # 초기 설정 스크립트 (Linux/macOS)
├── create_app.ps1       # 초기 설정 스크립트 (Windows)
├── run.sh               # 빠른 실행 래퍼 (Linux/macOS)
└── run.ps1              # 빠른 실행 래퍼 (Windows)

tests/                   # 테스트 스위트
config/                  # 설정 파일
docs/                    # 문서
```

## 설정

설정은 `./scripts/create_app.sh`에 의해 자동으로 설정되지만, 수동으로도 설정할 수 있습니다:

1. 예시 설정 파일 복사:
   ```bash
   cp config/dev.yaml.example config/dev.yaml
   ```

2. 설정을 반영하여 `config/dev.yaml` 편집

3. 시크릿 정보를 위한 환경 변수 설정:

   **Linux/macOS:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your-token"
   export TELEGRAM_CHAT_ID="your-chat-id"
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:TELEGRAM_BOT_TOKEN="your-token"
   $env:TELEGRAM_CHAT_ID="your-chat-id"
   ```

4. 운영 환경을 위해 `config/prod.yaml` 생성:
   ```bash
   cp config/dev.yaml.example config/prod.yaml
   # 운영 환경 설정으로 prod.yaml 편집
   ```

## 스크립트

### 설정 스크립트

초기 설정 스크립트 - 템플릿을 클론한 후 한 번만 실행하세요.

**Linux/macOS (`scripts/create_app.sh`):**
```bash
./scripts/create_app.sh           # 전체 설정
./scripts/create_app.sh --help    # 옵션 보기
```

**Windows (`scripts/create_app.ps1`):**
```powershell
.\scripts\create_app.ps1          # 전체 설정
.\scripts\create_app.ps1 -Help    # 옵션 보기
```

**기능:**
- Python 3.11+ 및 uv 설치 확인
- `uv sync --all-extras`로 모든 의존성 설치
- 예시 파일로부터 `config/dev.yaml` 생성
- `logs/` 디렉토리 설정
- pre-commit 훅 설치
- 초기 테스트 실행 (선택사항)

### 실행 스크립트

빠른 실행 래퍼 - 간편한 앱 실행 도구입니다.

**Linux/macOS (`scripts/run.sh`):**
```bash
./scripts/run.sh [MODE] [ENV]
./scripts/run.sh --help           # 사용법 보기

# 예시:
./scripts/run.sh                  # 시작 모드, 개발 환경
./scripts/run.sh batch            # 배치 모드, 개발 환경
./scripts/run.sh start prod       # 시작 모드, 운영 환경
```

**Windows (`scripts/run.ps1`):**
```powershell
.\scripts\run.ps1 [MODE] [ENV]
.\scripts\run.ps1 -Help           # 사용법 보기

# 예시:
.\scripts\run.ps1                 # 시작 모드, 개발 환경
.\scripts\run.ps1 batch           # 배치 모드, 개발 환경
.\scripts\run.ps1 start prod      # 시작 모드, 운영 환경
```

**기능:**
- uv 및 설정 파일 존재 확인
- 명확한 실행 정보 출력
- 로그 디렉토리 자동 생성
- 적절한 오류 메시지 및 종료 코드

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
