"""Notification model for Lexora Library."""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Notification(models.Model):
    """In-app notification for users."""

    class Type(models.TextChoices):
        LOAN_DUE = "loan_due", _("Vencimiento próximo")
        LOAN_OVERDUE = "loan_overdue", _("Préstamo vencido")
        LOAN_APPROVED = "loan_approved", _("Préstamo aprobado")
        LOAN_RETURNED = "loan_returned", _("Devolución confirmada")
        BOOK_AVAILABLE = "book_available", _("Libro disponible")
        FINE_ISSUED = "fine_issued", _("Multa generada")
        SYSTEM = "system", _("Sistema")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("usuario"),
    )

    type = models.CharField(
        _("tipo"),
        max_length=30,
        choices=Type.choices,
        default=Type.SYSTEM,
        db_index=True,
    )
    title = models.CharField(_("título"), max_length=200)
    message = models.TextField(_("mensaje"))
    is_read = models.BooleanField(_("leída"), default=False, db_index=True)

    # Optional reference
    loan_id = models.UUIDField(null=True, blank=True)
    book_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("notificación")
        verbose_name_plural = _("notificaciones")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self) -> str:
        return f"[{self.type}] {self.title} → {self.user.email}"

    def mark_read(self) -> None:
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])
