# Remove default.yaml Design

**Goal:** `config/default.yaml` 파일을 완전히 제거하고, 애플리케이션이 `config/dev.yaml` 또는 `config/prod.yaml` 단일 파일만으로 설정을 로드하도록 바꾼다.

**Decision:** 설정 로더는 `config/{env}.yaml` 한 파일만 읽는다. 누락된 값은 `Settings`와 하위 Pydantic 모델의 기본값으로 채우고, 더 이상 파일 간 deep merge를 수행하지 않는다.

## Scope

- `src/utils/config.py`에서 `default.yaml` 의존 제거
- 관련 테스트를 단일 환경 파일 기준으로 갱신
- 저장소 내 `default.yaml` 참조 문서/스크립트 정리
- `docs/task.md` 진행 상태 반영

## Behavior

- 성공 경로:
  - `load_config(env="dev")`는 `config/dev.yaml`만 읽는다.
  - YAML에 없는 필드는 `Settings` 기본값이 적용된다.
- 실패 경로:
  - `config/{env}.yaml`가 없으면 `ConfigurationError`를 유지한다.
  - YAML 구조나 값이 잘못되면 기존과 같이 Pydantic 검증 오류가 발생한다.

## Tradeoffs

- 장점:
  - 사용자가 편집할 설정 소스가 환경 파일 하나로 명확해진다.
  - `default.yaml` 누락/병합 관련 오류와 문서 부채가 사라진다.
- 단점:
  - 기존에 `default.yaml`에 있던 공통값은 각 환경 파일 또는 코드 기본값으로 옮겨야 한다.
  - 생성 스크립트가 프로젝트 이름 등을 갱신하던 대상 파일을 바꿔야 한다.

## Testing

- `tests/test_utils/test_config.py`에서:
  - 환경 파일 하나만 있을 때 로딩 성공
  - 환경 파일이 없을 때 명확한 실패
  - silent time 설정이 단일 파일 기준으로 유지되는지 검증
- 필요 시 스크립트 테스트에서 `default.yaml` 참조 제거 영향 확인
