"""Loans app configuration."""
from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.loans"
    verbose_name = "Sistema de Préstamos"

    def ready(self) -> None:
        import apps.loans.signals  # noqa: F401
