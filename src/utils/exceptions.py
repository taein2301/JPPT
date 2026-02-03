"""애플리케이션 커스텀 예외 정의.

예외 계층 구조:
- AppException (기본 예외)
  ├─ ConfigurationError (설정 오류)
  ├─ ServiceError (외부 서비스 오류)
  │  ├─ TelegramError (텔레그램 API 오류)
  │  └─ HttpClientError (HTTP 클라이언트 오류)
  ├─ ValidationError (데이터 검증 오류)
  └─ RetryExhaustedError (재시도 횟수 초과)
"""


class AppException(Exception):
    """모든 애플리케이션 오류의 기본 예외 클래스."""

    pass


class ConfigurationError(AppException):
    """설정 파일 또는 환경 변수 관련 오류.

    설정 파일이 없거나, 잘못된 형식이거나, 필수 값이 누락된 경우 발생합니다.
    """

    pass


class ServiceError(AppException):
    """외부 서비스 연동 중 발생하는 오류.

    API 호출 실패, 네트워크 오류, 타임아웃 등 외부 의존성 문제를 나타냅니다.
    """

    pass


class TelegramError(ServiceError):
    """텔레그램 API 호출 중 발생하는 오류.

    봇 토큰 오류, 메시지 전송 실패, API 제한 초과 등의 경우 발생합니다.
    """

    pass


class HttpClientError(ServiceError):
    """HTTP 클라이언트 요청 중 발생하는 오류.

    연결 실패, HTTP 상태 코드 오류, 타임아웃 등의 경우 발생합니다.
    """

    pass


class ValidationError(AppException):
    """데이터 검증 실패 시 발생하는 오류.

    입력 데이터가 예상 형식이나 제약 조건을 만족하지 않을 때 발생합니다.
    """

    pass


class RetryExhaustedError(AppException):
    """재시도 횟수가 모두 소진된 경우 발생하는 오류.

    설정된 최대 재시도 횟수만큼 시도했지만 여전히 실패한 경우 발생합니다.
    """

    pass
