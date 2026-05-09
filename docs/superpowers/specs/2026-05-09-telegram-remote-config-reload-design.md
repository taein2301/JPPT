# Telegram Remote Config Reload Design

작성일: 2026-05-09

## 목적

JPPT `start` 모드에서 Telegram 명령으로 설정을 수동 reload할 수 있게 한다. `batch` 모드는 일회성 실행이므로 제외한다.

## 확인된 현재 구조

- `start` 명령은 실행 시작 시 `_load_settings(env, config)`를 호출해 설정을 한 번 로드한다. 근거: `src/main.py`.
- 로드된 `Settings` 객체는 `run_app(settings, env)`로 전달된다. 근거: `src/main.py`.
- `run_app`는 현재 `TelegramNotifier`를 생성하고, 5초 sleep 기반 템플릿 루프를 돈다. 루프 중 설정 reload 경로는 없다. 근거: `src/utils/app_runner.py`.
- 현재 `TelegramNotifier`는 `send_message()` 송신 전용이다. Telegram update 수신이나 command handler는 없다. 근거: `src/utils/telegram.py`.
- `setup_logger()`는 기존 Loguru handler를 제거하고 콘솔/파일 handler를 새로 추가한다. logging 설정을 reload 대상에 넣으면 logger 재설정이 필요하다. 근거: `src/utils/logger.py`.
- 런타임 의존성은 `python-telegram-bot>=21.0`이고, 현재 lock 파일에는 `python-telegram-bot` 22.6이 기록되어 있다. 근거: `pyproject.toml`, `uv.lock`.

## 외부 문서 근거

- `python-telegram-bot` 22.6의 `CommandHandler`는 `/`로 시작하는 Telegram command message를 처리한다. 출처: https://docs.python-telegram-bot.org/en/v22.6/telegram.ext.commandhandler.html
- `python-telegram-bot` 22.6 문서는 다른 asyncio framework와 함께 사용할 때 `Application.run_polling()`이 event loop를 block할 수 있으므로 수동 start/stop 조합을 고려하라고 설명한다. 출처: https://docs.python-telegram-bot.org/en/v22.6/telegram.ext.application.html

## 범위

### 포함

- `start` 모드 전용 Telegram 원격제어
- `/reload`, `/status`, `/help` command
- 허용된 Telegram chat id 기반 접근 제어
- reload 실패 시 기존 설정 유지
- reload 성공 시 logging 설정과 Telegram 설정 재적용
- reload 결과 Telegram 응답 및 로그 기록

### 제외

- `batch` 모드 원격제어
- Telegram webhook
- 로컬 signal 기반 reload
- `run.sh reload`
- 임의 shell command 실행
- 설정 파일 수정 기능
- 매수/매도/거래 같은 도메인 명령
- 허용 chat id가 비어 있는 상태에서 원격제어 활성화

## 설정 모델

`TelegramConfig` 아래에 remote control 설정을 추가한다.

```yaml
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
  silent_time:
    enabled: false
    start: "23:00"
    end: "08:00"
    timezone: "Asia/Seoul"
  remote_control:
    enabled: false
    allowed_chat_ids: []
    commands:
      reload: true
      status: true
      help: true
```

규칙:

- `remote_control.enabled: true`이면 `telegram.enabled`, `bot_token`, `allowed_chat_ids`가 유효해야 한다.
- `allowed_chat_ids`는 문자열 리스트로 저장한다. Telegram chat id는 숫자처럼 보일 수 있지만 config와 비교 안정성을 위해 문자열로 정규화한다.
- `remote_control.enabled` 기본값은 반드시 `false`다.

## 컴포넌트 설계

### `TelegramNotifier`

역할은 유지한다.

- 송신 전용
- 시작/중지/reload 결과 알림 전송
- silent time 적용
- 전송 실패가 앱 실행을 중단하지 않음

### `TelegramRemoteController`

새 컴포넌트로 분리한다.

책임:

- `ApplicationBuilder`로 Telegram polling application 생성
- `CommandHandler`로 `/reload`, `/status`, `/help` 등록
- chat id 접근 제어
- 허용된 command를 app runtime에 요청으로 전달
- 시작/정지 lifecycle 관리

금지:

- 설정을 직접 교체하지 않는다.
- logger를 직접 재설정하지 않는다.
- 비즈니스 루프를 직접 중단하지 않는다.

### `ReloadCoordinator`

app runtime 내부 상태를 관리한다.

상태:

- `current_settings`
- `env`
- `config_dir`
- `reload_count`
- `last_reload_status`
- `last_reload_at`
- `last_reload_error`

책임:

- `/reload` 요청을 queue/event로 수신
- 안전한 loop 지점에서 `load_config()` 재실행
- 성공 시 설정 교체와 runtime dependency 재생성
- 실패 시 기존 설정 유지
- 결과 메시지 생성

## 명령 동작

### `/reload`

1. command 수신
2. chat id를 문자열로 변환
3. `allowed_chat_ids`에 없으면 거부
4. 허용된 command이면 reload 요청 enqueue
5. 앱 루프가 요청을 처리
6. 새 config load 및 Pydantic validation 수행
7. 성공 시:
   - `current_settings` 교체
   - logger 재설정
   - notifier 재생성
   - remote controller 설정 재반영
   - `reload_count += 1`
   - Telegram 응답: reload success
8. 실패 시:
   - 기존 설정 유지
   - `last_reload_status=failed`
   - error type/message 기록
   - Telegram 응답: reload failed

### `/status`

응답 항목:

- app name
- env
- uptime
- remote control enabled 여부
- reload count
- last reload status
- last reload at
- last reload error type, 실패한 경우만

secret 값은 출력하지 않는다.

### `/help`

활성화된 command만 표시한다.

## 보안 규칙

- `remote_control.enabled: false`가 기본값이다.
- `remote_control.enabled: true`이고 `allowed_chat_ids`가 비어 있으면 설정 검증 실패로 처리한다.
- 무단 chat id의 command는 실행하지 않는다.
- 무단 chat에 상세 오류나 app 상태를 응답하지 않는다.
- Telegram token, chat id, config secret은 로그 summary에서 마스킹한다.
- 원격제어 명령은 allowlist 방식만 허용한다.
- 자유 텍스트 명령이나 shell command 실행은 금지한다.

## 오류 처리

- config 파일 없음, YAML parse 실패, Pydantic validation 실패는 reload 실패로 처리한다.
- reload 실패는 앱 종료 사유가 아니다.
- logger 재설정 실패는 reload 실패로 처리하고 기존 logger/settings를 유지한다.
- Telegram 응답 실패는 reload 성공/실패 판정에 영향을 주지 않는다.
- reload 결과 응답은 reload를 요청한 command context로 보낸다. 새 설정에서 remote control이 꺼지더라도 요청자에게 최종 결과는 응답한다.

## Config Source 주의점

현재 CLI의 `--config`는 파일 경로를 그대로 읽지 않고 `Path(config).parent`만 사용해 다시 `{env}.yaml`을 읽는 구조다. 이 상태를 유지하면 `/reload`도 같은 계약을 따른다.

정확한 파일 경로 reload는 이 설계 범위가 아니다. 이 설계는 기존 `load_config(env, config_dir)` 계약을 유지한다.

## 테스트 계획

- config model 기본값: remote control disabled
- remote control enabled인데 `allowed_chat_ids`가 비어 있으면 config validation 실패
- 허용 chat id의 `/reload` 요청이 reload queue에 들어가는지
- 무단 chat id의 `/reload` 요청이 무시되는지
- reload 성공 시 settings/logger/notifier 상태가 갱신되는지
- reload 실패 시 기존 settings가 유지되는지
- `/status`가 secret 없이 상태를 반환하는지
- `batch` command는 remote controller를 시작하지 않는지
- 기존 `TelegramNotifier.send_message()` 송신 테스트가 깨지지 않는지

## 승인 기준

- `uv run pytest --no-cov` 통과
- `uv run ruff check src tests` 통과
- `uv run mypy src --exclude src/logs` 통과
- `start` 모드에서 Telegram `/reload` 성공/실패가 로그와 Telegram 응답으로 확인됨
- unauthorized chat id에서 reload가 실행되지 않음
