from typing import Any

from fastapi import status


class AppError(Exception):
    """
    Base exception for all application-specific errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or "INTERNAL_SERVER_ERROR"
        self.details = details or {}


class EntityNotFoundError(AppError):
    """
    Raised when a requested resource is not found.
    """

    def __init__(
        self,
        entity_name: str,
        entity_id: Any,
        message: str | None = None,
    ):
        message = message or f"{entity_name} with id {entity_id} not found."
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details={"entity": entity_name, "id": entity_id},
        )


class AuthenticationError(AppError):
    """
    Raised when authentication fails.
    """

    def __init__(self, message: str = "Authentication failed."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
        )


class AuthorizationError(AppError):
    """
    Raised when a user does not have permission to access a resource.
    """

    def __init__(self, message: str = "Permission denied."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="UNAUTHORIZED",
        )


class ValidationError(AppError):
    """
    Raised when input validation fails.
    """

    def __init__(
        self, message: str = "Validation error.", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            details=details,
        )


class ConflictError(AppError):
    """
    Raised when a conflict occurs (e.g., duplicate entry).
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            details=details,
        )
