"""Custom middleware for Lexora Library."""
import logging
import time
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from typing import Callable

logger = logging.getLogger("lexora.middleware")


class ActivityLogMiddleware:
    """Log user activity for auditing purposes."""

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start_time

        # Only log authenticated API requests
        if request.path.startswith("/api/") and hasattr(request, "user") and request.user.is_authenticated:
            logger.info(
                "API | %s %s | user=%s | status=%d | %.3fs",
                request.method,
                request.path,
                request.user.email,
                response.status_code,
                duration,
            )
        return response


class RateLimitMiddleware:
    """Basic IP-based rate limiting for unauthenticated requests."""

    LIMIT = 200  # requests per minute for anonymous users
    WINDOW = 60  # seconds

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only rate-limit unauthenticated API requests
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)

        ip = self._get_client_ip(request)
        cache_key = f"ratelimit:{ip}"
        count = cache.get(cache_key, 0)

        if count >= self.LIMIT:
            return JsonResponse(
                {
                    "status": "error",
                    "code": "rate_limit_exceeded",
                    "message": "Demasiadas solicitudes. Intenta de nuevo en un minuto.",
                },
                status=429,
            )

        cache.set(cache_key, count + 1, self.WINDOW)
        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
