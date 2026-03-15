# Generated AGENTS Template Design

## Goal

`scripts/create_app.sh`로 새 프로젝트를 만들 때, 생성된 프로젝트 루트에 전용 `AGENTS.md`를 자동 배치한다. 이 문서는 템플릿 원본 보호 규칙과 `src/utils/` 변경 제한을 명시해야 한다.

## Current Context

- 현재 템플릿 루트의 `AGENTS.md`는 JPPT 템플릿 자체를 유지보수할 때의 지침이다.
- `scripts/create_app.sh`는 템플릿 복사 시 `docs/` 전체를 제외하므로, 생성 프로젝트용 문서는 별도 복사 단계가 필요하다.
- 생성 스크립트 테스트는 현재 없다.

## Chosen Approach

`docs/` 아래에 생성 프로젝트 전용 AGENTS 템플릿 파일을 추가하고, `scripts/create_app.sh`가 프로젝트 복사 후 이 파일을 루트 `AGENTS.md`로 복사한다.

이 접근을 선택한 이유:
- 생성 프로젝트용 규칙을 템플릿 개발용 `AGENTS.md`와 분리할 수 있다.
- 문서 내용을 스크립트에 inline 하지 않아 유지보수가 쉽다.
- 스크립트에서 복사만 수행하므로 구현 diff가 작다.

## Rules In Generated AGENTS.md

- 템플릿이 제공한 JPPT 원본 파일은 수정 금지
- `src/utils/`에는 신규 파일 생성 금지
- `src/utils/`에는 파일 삭제 금지
- 확장은 `src/core/`, 설정, CLI 진입점 같은 의도된 확장 지점 위주로 유도

## Testing Strategy

- `create_app.sh`를 임시 디렉터리에서 실행하는 좁은 pytest 통합 테스트 추가
- 외부 의존성(`gh`, `uv`, 일부 `git`)은 가짜 실행 파일로 대체
- 생성된 프로젝트 루트에 `AGENTS.md`가 생겼는지 확인
- 생성된 `AGENTS.md`에 요구 규칙 문구가 들어있는지 확인
