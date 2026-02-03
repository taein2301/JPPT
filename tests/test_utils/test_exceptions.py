from jppt.utils.exceptions import (
    AppException,
    ConfigurationError,
    HttpClientError,
    RetryExhaustedError,
    ServiceError,
    TelegramError,
    ValidationError,
)


def test_app_exception_with_message() -> None:
    exc = AppException("test error")
    assert str(exc) == "test error"
    assert exc.args == ("test error",)


def test_exception_hierarchy() -> None:
    """Test that all exceptions inherit from AppException."""
    assert issubclass(ConfigurationError, AppException)
    assert issubclass(ServiceError, AppException)
    assert issubclass(TelegramError, ServiceError)
    assert issubclass(HttpClientError, ServiceError)
    assert issubclass(ValidationError, AppException)
    assert issubclass(RetryExhaustedError, AppException)


def test_configuration_error() -> None:
    exc = ConfigurationError("config missing")
    assert str(exc) == "config missing"
    assert isinstance(exc, AppException)


def test_service_error() -> None:
    exc = ServiceError("service down")
    assert str(exc) == "service down"
    assert isinstance(exc, AppException)


def test_telegram_error() -> None:
    exc = TelegramError("telegram api error")
    assert str(exc) == "telegram api error"
    assert isinstance(exc, ServiceError)


def test_http_client_error() -> None:
    exc = HttpClientError("http request failed")
    assert str(exc) == "http request failed"
    assert isinstance(exc, ServiceError)
