"""Custom exception handling for Lexora Library API."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

logger = logging.getLogger("lexora.exceptions")


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns a consistent error envelope.

    Format:
        {
            "status": "error",
            "code": "error_code",
            "message": "Human readable message",
            "details": {...}  # optional
        }
    """
    # Let DRF handle first
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "status": "error",
            "code": _get_error_code(exc),
            "message": _get_error_message(response.data),
            "details": response.data,
        }
        response.data = error_data
        logger.warning(
            "API error: %s | Path: %s | User: %s",
            exc.__class__.__name__,
            context["request"].path,
            getattr(context["request"].user, "email", "anonymous"),
        )
        return response

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "status": "error",
                "code": "validation_error",
                "message": "Error de validación",
                "details": exc.message_dict if hasattr(exc, "message_dict") else {"error": exc.messages},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Unhandled → 500
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return Response(
        {
            "status": "error",
            "code": "internal_error",
            "message": "Error interno del servidor",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_code(exc) -> str:
    code_map = {
        "AuthenticationFailed": "authentication_failed",
        "NotAuthenticated": "not_authenticated",
        "PermissionDenied": "permission_denied",
        "NotFound": "not_found",
        "MethodNotAllowed": "method_not_allowed",
        "Throttled": "rate_limit_exceeded",
        "ValidationError": "validation_error",
    }
    return code_map.get(exc.__class__.__name__, "error")


def _get_error_message(data) -> str:
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        if "non_field_errors" in data:
            errors = data["non_field_errors"]
            return str(errors[0]) if errors else "Error de validación"
        return "Error de validación en los datos enviados"
    if isinstance(data, list):
        return str(data[0]) if data else "Error"
    return str(data)


class LexoraException(Exception):
    """Base exception for Lexora business logic errors."""

    def __init__(self, message: str, code: str = "lexora_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class BookNotAvailableError(LexoraException):
    """Raised when a book has no available stock."""

    def __init__(self, book_title: str):
        super().__init__(
            f"El libro '{book_title}' no está disponible para préstamo.",
            code="book_not_available",
        )


class LoanLimitExceededError(LexoraException):
    """Raised when a user reaches their loan limit."""

    def __init__(self, limit: int):
        super().__init__(
            f"Has alcanzado el límite máximo de {limit} préstamos activos.",
            code="loan_limit_exceeded",
        )


class UserHasOverdueLoanError(LexoraException):
    """Raised when a user tries to borrow with overdue loans."""

    def __init__(self):
        super().__init__(
            "Tienes préstamos vencidos. Devuelve los libros pendientes antes de solicitar nuevos préstamos.",
            code="user_has_overdue_loans",
        )


class LoanAlreadyReturnedError(LexoraException):
    """Raised when trying to return an already returned loan."""

    def __init__(self):
        super().__init__(
            "Este préstamo ya fue devuelto anteriormente.",
            code="loan_already_returned",
        )


class RenewalLimitExceededError(LexoraException):
    """Raised when renewal limit is reached."""

    def __init__(self, limit: int):
        super().__init__(
            f"Este préstamo ya alcanzó el límite de {limit} renovaciones.",
            code="renewal_limit_exceeded",
        )
