# create_app Telegram setup design

## Goal

`scripts/create_app.sh` 실행 중 생성 프로젝트에 `config/dev.yaml`을 확실히 만들고, Telegram 설정이 완료되면 `<app-name> create 성공` 테스트 메시지 1건을 즉시 전송한다.

## Context

- 생성 스크립트는 템플릿 복사 후 `install_deps`, `setup_config`, `setup_dirs`, `install_hooks`, `setup_telegram_optional` 순서로 실행된다.
- `setup_config`는 이미 `config/dev.yaml.example`을 `config/dev.yaml`로 복사하는 로직을 갖고 있다.
- Telegram 설정 함수는 현재 `config/default.yaml`만 수정하고, 저장 후 테스트 메시지를 보내지 않는다.

## Options

### Option 1: 기존 흐름에 직접 추가

- `setup_config`를 그대로 사용해 `config/dev.yaml` 생성을 보장한다.
- `setup_telegram_optional` 내부에서 설정 저장 직후 `sendMessage` API 호출을 추가한다.

장점:
- 변경 범위가 가장 작다.
- 현재 인터랙티브 흐름을 유지한다.
- 사용자가 설정 직후 성공 여부를 바로 확인할 수 있다.

단점:
- Telegram 설정 함수가 저장과 전송 둘 다 담당한다.

### Option 2: 별도 테스트 메시지 함수 분리

- 설정 저장은 기존 함수에서 처리한다.
- 성공 메시지는 별도 `send_telegram_test_message` 함수에서 호출한다.

장점:
- 책임 분리가 조금 더 명확하다.

단점:
- 함수 수만 늘고, 현재 스크립트 규모에서는 이점이 작다.

## Decision

Option 1을 사용한다. 작은 셸 스크립트에서는 흐름을 단순하게 유지하는 편이 낫고, 요구사항도 "설정 끝나면 바로 1건 보내기"이므로 저장 직후 전송이 가장 자연스럽다.

## Behavior

- 프로젝트 생성 후 설치 단계에서 `setup_config`가 실행되면 `config/dev.yaml.example`이 있으면 `config/dev.yaml`을 생성한다.
- 사용자가 Telegram Bot Token과 Chat ID를 입력하면:
  - `config/default.yaml`의 Telegram 설정을 갱신한다.
  - 이어서 Telegram `sendMessage` API로 `<app-name> create 성공` 메시지를 보낸다.
- 메시지 전송 성공 여부는 stdout에 표시한다.
- 메시지 전송 실패는 경고로 알리되, 이미 프로젝트 설정은 끝난 상태이므로 전체 생성 작업 자체를 실패로 되돌리지는 않는다.

## Testing

- 스크립트 통합 테스트에 다음을 추가한다.
  - Telegram 설정 후 `config/dev.yaml`이 생성되는지 확인
  - Telegram `sendMessage` 호출이 발생하는지 확인
  - 메시지 본문에 앱명과 `create 성공` 문자열이 포함되는지 확인
