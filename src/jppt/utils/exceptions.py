"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(AppException):
    """Exception raised for configuration-related errors."""

    pass


class ServiceError(AppException):
    """Exception raised for external service errors."""

    pass


class TelegramError(ServiceError):
    """Exception raised for Telegram API errors."""

    pass


class HttpClientError(ServiceError):
    """Exception raised for HTTP client errors."""

    pass


class ValidationError(AppException):
    """Exception raised for data validation errors."""

    pass


class RetryExhaustedError(AppException):
    """Exception raised when retry attempts are exhausted."""

    pass
