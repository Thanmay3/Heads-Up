class ServiceError(Exception):
    """Base for expected service-level failures mapped to HTTP status codes."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""

    status_code = 404


class ConflictError(ServiceError):
    """Raised when a request would duplicate existing state."""

    status_code = 409


class MaterialValidationError(ServiceError):
    """Raised when an uploaded material fails input validation."""

    status_code = 422


class MaterialTooLargeError(ServiceError):
    """Raised when an uploaded file exceeds the configured size limit."""

    status_code = 413
