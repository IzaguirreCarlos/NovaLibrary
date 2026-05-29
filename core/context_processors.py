"""Global context processors for Lexora Library templates."""
from django.conf import settings
from django.http import HttpRequest


def global_context(request: HttpRequest) -> dict:
    """Inject global variables into all templates."""
    context = {
        "APP_NAME": "Lexora Library",
        "APP_VERSION": "1.0.0",
        "DEBUG": settings.DEBUG,
    }

    if request.user.is_authenticated:
        # Inject unread notification count
        from apps.notifications.models import Notification
        context["unread_notifications_count"] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        # Active loan count
        from apps.loans.models import Loan
        context["active_loans_count"] = Loan.objects.filter(
            user=request.user, status=Loan.Status.BORROWED
        ).count()

    return context
