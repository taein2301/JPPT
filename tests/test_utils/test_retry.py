import pytest

from src.utils.exceptions import RetryExhaustedError
from src.utils.retry import with_retry


def test_retry_succeeds_on_first_attempt() -> None:
    call_count = 0

    @with_retry(max_attempts=3, wait_seconds=0.01)
    def succeeds_immediately() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = succeeds_immediately()
    assert result == "success"
    assert call_count == 1


def test_retry_succeeds_after_failures() -> None:
    call_count = 0

    @with_retry(max_attempts=3, wait_seconds=0.01)
    def fails_twice() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("temporary error")
        return "success"

    result = fails_twice()
    assert result == "success"
    assert call_count == 3


def test_retry_exhausted() -> None:
    @with_retry(max_attempts=2, wait_seconds=0.01)
    def always_fails() -> str:
        raise ValueError("permanent error")

    with pytest.raises(RetryExhaustedError) as exc_info:
        always_fails()

    assert "permanent error" in str(exc_info.value)
