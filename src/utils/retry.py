"""tenacity를 사용한 재시도 데코레이터.

이 모듈은 실패한 함수 호출을 자동으로 재시도하는 데코레이터를 제공합니다.
지수 백오프(exponential backoff)를 사용하여 재시도 간격을 점진적으로 늘립니다.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from loguru import logger
from tenacity import (
    RetryError,
    Retrying,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.exceptions import RetryExhaustedError

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    max_wait_seconds: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """지수 백오프를 사용하는 재시도 데코레이터.

    함수 실행에 실패하면 지정된 횟수만큼 자동으로 재시도합니다.
    재시도 간격은 지수적으로 증가하며 최대 대기 시간을 초과하지 않습니다.

    Args:
        max_attempts: 최대 재시도 횟수
        wait_seconds: 초기 재시도 대기 시간 (초)
        max_wait_seconds: 최대 재시도 대기 시간 (초)

    Returns:
        실패 시 재시도하는 데코레이트된 함수

    Raises:
        RetryExhaustedError: 모든 재시도 횟수가 소진된 경우
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result: T | None = None
            try:
                # tenacity의 Retrying 컨텍스트 매니저 사용
                for attempt in Retrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=wait_seconds,
                        max=max_wait_seconds,
                    ),
                ):
                    with attempt:
                        result = func(*args, **kwargs)
                        return result
            except RetryError as e:
                # RetryError에서 원본 예외 추출
                original_error = e.last_attempt.exception()
                logger.error(
                    f"Retry exhausted for {func.__name__} "
                    f"after {max_attempts} attempts: {original_error}"
                )
                raise RetryExhaustedError(
                    f"Failed after {max_attempts} attempts: {original_error}"
                ) from original_error
            except Exception as e:
                # 기타 예외 처리 및 래핑
                logger.error(
                    f"Retry exhausted for {func.__name__} after {max_attempts} attempts: {e}"
                )
                raise RetryExhaustedError(f"Failed after {max_attempts} attempts: {e}") from e
            # 여기에 도달하면 안 되지만 mypy 만족을 위해 추가
            raise RetryExhaustedError(f"Unexpected end of retry logic for {func.__name__}")

        return wrapper

    return decorator
