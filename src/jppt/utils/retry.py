"""Retry decorator using tenacity."""

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

from jppt.utils.exceptions import RetryExhaustedError

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    max_wait_seconds: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_seconds: Initial wait time between retries
        max_wait_seconds: Maximum wait time between retries

    Returns:
        Decorated function that retries on failure

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=wait_seconds,
                        max=max_wait_seconds,
                    ),
                ):
                    with attempt:
                        return func(*args, **kwargs)
            except RetryError as e:
                # Extract the original exception from RetryError
                original_error = e.last_attempt.exception()
                logger.error(
                    f"Retry exhausted for {func.__name__} "
                    f"after {max_attempts} attempts: {original_error}"
                )
                raise RetryExhaustedError(
                    f"Failed after {max_attempts} attempts: {original_error}"
                ) from original_error
            except Exception as e:
                # Catch any other exception and wrap it
                logger.error(
                    f"Retry exhausted for {func.__name__} after {max_attempts} attempts: {e}"
                )
                raise RetryExhaustedError(f"Failed after {max_attempts} attempts: {e}") from e

        return wrapper

    return decorator
