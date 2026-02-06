# PRD: JPPT 

## 1. 개요

### 1.1 프로젝트 명
JPPT JKLEE Python Project Template

### 1.2 목적
확장 가능한 Python 애플리케이션을 빠르게 구축하기 위한 범용 보일러플레이트 템플릿을 제공한다. 현대적인 Python 스택을 기반으로 하며, 새로운 프로젝트의 뼈대로 활용되어 개발 생산성을 극대화한다.

### 1.3 대상 사용자
- Python 기반 CLI 애플리케이션 개발자
- 자동화 봇/배치 작업 개발자
- 빠른 프로토타이핑이 필요한 개발자

---

## 2. 핵심 기술 스택

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| 패키지 관리 | uv | latest | 의존성 관리 및 가상환경 |
| CLI | Typer | ^0.9.0 | 커맨드 라인 인터페이스 |
| 설정 관리 | Pydantic Settings | ^2.0 | 타입 안전한 설정 |
| 로깅 | Loguru | ^0.7.0 | 구조화된 로깅 |
| HTTP | httpx | ^0.27.0 | 비동기 HTTP 클라이언트 |
| 재시도 | tenacity | ^8.0 | 재시도 로직 |
| 알림 | python-telegram-bot | ^21.0 | Telegram 연동 |
| 린팅 | ruff | latest | 코드 품질 |
| 타입체크 | mypy | latest | 정적 타입 검사 |
| 테스트 | pytest | ^8.0 | 단위 테스트 |
| Git Hooks | pre-commit | latest | 커밋 전 자동 검사 |

---

## 3. 프로젝트 구조

```
JPPT/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI 진입점 (Typer)
│   ├── core/                # 핵심 비즈니스 로직
│   │   └── __init__.py
│   └── utils/               # 공통 유틸리티
│       ├── __init__.py
│       ├── config.py        # 설정 관리 (Pydantic)
│       ├── logger.py        # 로깅 설정 (Loguru, 날짜 기반 로테이션)
│       ├── app_runner.py    # App 모드 실행 (상주)
│       ├── batch_runner.py  # Batch 모드 실행 (일회성)
│       ├── exceptions.py    # 커스텀 예외
│       ├── retry.py         # 재시도 데코레이터
│       ├── signals.py       # Graceful Shutdown
│       ├── http_client.py   # HTTP 클라이언트
│       └── telegram.py      # Telegram 연동
│
├── tests/                   # 테스트
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_main.py         # CLI 테스트
│   ├── test_integration.py  # 통합 테스트
│   ├── test_core/
│   │   └── __init__.py
│   └── test_utils/
│       └── __init__.py
├── config/                  # 설정 파일
│   ├── default.yaml         # 기본값 + 스키마 (커밋)
│   ├── dev.yaml.example     # 개발 환경 예시 (커밋)
│   ├── dev.yaml             # 개발 환경 설정 (gitignore)
│   └── prod.yaml            # 운영 환경 설정 (gitignore)
├── logs/                    # 로그 파일 (gitignore)
├── docs/                    # 문서
│   ├── FRAMEWORK_GUIDE.md
│   └── PRD.md
├── scripts/                 # 프로젝트 생성기
│   ├── create_app.sh        # 프로젝트 생성 스크립트 (Linux/macOS)
│   └── create_app.ps1       # 프로젝트 생성 스크립트 (Windows)
├── run.sh                   # 실행 래퍼 (Linux/macOS)
├── run.ps1                  # 실행 래퍼 (Windows)
├── .pre-commit-config.yaml  # pre-commit 설정
├── pyproject.toml           # 프로젝트 메타데이터
├── ruff.toml                # ruff 설정
├── .gitignore
├── .gitattributes           # merge 전략
├── README.md
└── README.ko.md
```

---

## 4. 기능 요구사항

### 4.1 CLI 인터페이스 (Typer)

#### 4.1.1 명령어 구조
```bash
# App 모드: 상주 실행 (Ctrl+C로 종료)
python -m src.main start [OPTIONS]

# Batch 모드: 일회성 실행 후 종료
python -m src.main batch [OPTIONS]

# 버전 확인
python -m src.main --version
```

#### 4.1.2 공통 옵션
| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--env` | `-e` | 환경 선택 (dev/prod) | dev |
| `--config` | `-c` | 설정 파일 경로 | config/{env}.yaml |
| `--log-level` | `-l` | 로그 레벨 | INFO |
| `--verbose` | `-v` | 상세 출력 | False |

---

### 4.2 설정 관리 (Pydantic Settings)

#### 4.2.1 설정 파일 구조
```
config/
├── default.yaml             # 기본값 + 스키마 (커밋)
├── dev.yaml.example         # 개발 환경 예시 (커밋)
├── dev.yaml                 # 개발 환경 실제 사용 (gitignore)
└── prod.yaml                # 운영 환경 실제 사용 (gitignore)
```

```yaml
# config/default.yaml (기본값, 커밋)
app:
  name: "my-app"
  version: "0.1.0"
  debug: false

logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
  rotation: "00:00"
  retention: "10 days"

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""

# config/dev.yaml.example (개발 예시, 커밋)
app:
  debug: true

telegram:
  enabled: false

# config/dev.yaml (실제 사용, gitignore)
app:
  debug: true

logging:
  level: "DEBUG"

telegram:
  enabled: false

# config/prod.yaml (실제 사용, gitignore)
app:
  debug: false

logging:
  level: "INFO"

telegram:
  enabled: true
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"
```

#### 4.2.2 설정 로드 순서
1. `config/default.yaml` — 기본값 및 스키마 (git 커밋)
2. `config/{env}.yaml` — 환경별 오버라이드 (gitignore, deep merge)
3. 환경변수 — 최종 오버라이드 (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)

#### 4.2.3 설정 클래스
- Pydantic BaseSettings 기반 타입 검증
- `AppConfig`, `LoggingConfig`, `TelegramConfig` 하위 모델
- `load_config(env, config_dir)` 함수로 계층적 병합

---

### 4.3 로깅 시스템 (Loguru)

#### 4.3.1 콘솔 출력
- 컬러 포맷 지원
- 출력 형식: `{time} | {level} | {file}:{line} | {message}`
- LOG_LEVEL 설정에 따른 필터링

#### 4.3.2 파일 저장
| 항목 | 설정 |
|------|------|
| 경로 | `logs/` |
| 현재 로그 | `{app_name}.log` (배치: `{app_name}_batch.log`) |
| 로테이션 파일명 | `{app_name}_{YYYYMMDD}.log` (커스텀 namer 사용) |
| 로테이션 | 매일 00:00 |
| 보존 기간 | 10일 (커스텀 retention handler) |
| 압축 | 비활성화 |

---

### 4.4 에러 핸들링

#### 4.4.1 커스텀 예외 계층
```python
AppException (Base)
├── ConfigurationError      # 설정 관련 오류
├── ServiceError           # 외부 서비스 오류
│   ├── TelegramError
│   └── HttpClientError
├── ValidationError        # 데이터 검증 오류
└── RetryExhaustedError    # 재시도 소진
```

#### 4.4.2 재시도 로직 (tenacity)
- 기본 재시도: 3회
- 백오프: 지수 (1s, 2s, 4s)
- 재시도 대상: 네트워크 오류, 일시적 서비스 오류

---

### 4.5 Graceful Shutdown

#### 4.5.1 요구사항
- SIGTERM, SIGINT 시그널 핸들링
- 진행 중인 작업 완료 대기 (타임아웃: 30초)
- 리소스 정리 (DB 연결, HTTP 세션 등)
- 종료 로그 기록

#### 4.5.2 구현 방식
```python
# App 모드에서 활용
async def shutdown():
    logger.info("Shutdown signal received")
    # 1. 새 작업 수락 중지
    # 2. 진행 중 작업 완료 대기
    # 3. 리소스 정리
    # 4. 종료
```

---

### 4.6 외부 서비스 연동

#### 4.6.1 Telegram
- 메시지 전송 (텍스트, 마크다운)
- 에러 알림 전송
- 비활성화 가능 (`telegram.enabled: false`)
- 인터랙티브 설정: `create_app.sh` 실행 시 Bot Token 입력 및 Chat ID 자동 조회
- 설정 저장: `config/default.yaml`에 직접 저장 또는 환경변수 오버라이드

#### 4.6.3 HTTP Client
- httpx 기반 비동기 클라이언트
- 기본 타임아웃 설정 (connect: 5s, read: 30s)
- 재시도 로직 내장
- 세션 관리

---

### 4.7 코드 품질

#### 4.7.1 Ruff 설정
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

#### 4.7.2 Mypy 설정
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
show_error_codes = true
```

#### 4.7.3 Pre-commit Hooks
1. ruff (lint + format)
2. mypy (type check)
3. pytest (빠른 단위 테스트만, 통합 테스트는 CI)

---

### 4.8 테스트

#### 4.8.1 구조
- `tests/conftest.py`: 공통 fixture
- `tests/test_utils/`: 유틸리티 테스트
- `tests/test_core/`: 비즈니스 로직 테스트

#### 4.8.2 Pytest 설정
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
    "--strict-markers",
    "-v"
]
```

#### 4.8.3 Fixtures
- `config`: 테스트용 설정 객체
- `mock_telegram`: Telegram 모킹
- `mock_http_client`: HTTP 클라이언트 모킹

---

## 5. Git 관리 전략

### 5.1 Upstream 방식
```
[python-app-template] (upstream)
       ↓ fork
[my-specific-app] (origin)
```

### 5.2 .gitattributes
```gitattributes
# 앱별로 다른 파일은 ours 전략
src/core/** merge=ours
src/utils/app_runner.py merge=ours
src/utils/batch_runner.py merge=ours
config/*.yaml merge=ours
README.md merge=ours
```

### 5.3 템플릿 업데이트 워크플로우
```bash
git remote add upstream <template-repo-url>
git fetch upstream
git merge upstream/main --allow-unrelated-histories
# 충돌 해결 후 커밋
```

---

## 6. 비기능 요구사항

### 6.1 성능
- App 시작 시간: < 2초
- 메모리 사용량: < 100MB (idle)

### 6.2 호환성
- Python 버전: 3.11+
- OS: Linux, macOS, Windows

### 6.3 확장성
- 새 서비스 추가 용이 (`utils/` 하위)
- 비즈니스 로직 분리 (`core/` 하위)

---

## 7. 제외 항목 (향후 추가 가능)
- [ ] Supabase 연동
- [ ] Docker 배포
- [ ] 스케줄러 (APScheduler)
- [ ] 모니터링/메트릭
- [ ] 웹 대시보드 (Streamlit)

---

## 8. 용어 정의

| 용어 | 설명 |
|------|------|
| App 모드 | 종료 신호까지 계속 실행되는 상주 프로세스 |
| Batch 모드 | 로직 수행 후 자동 종료되는 일회성 실행 |
| Graceful Shutdown | 진행 중인 작업을 안전하게 마무리하고 종료 |
| Upstream | 템플릿 원본 저장소 |
