"""
Loan model for Lexora Library.

Manages the full lifecycle of book loans: borrowed → returned / overdue / cancelled.
Auto-calculates fines for overdue returns.
"""
import uuid
import datetime as dt
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator


class LoanManager(models.Manager):
    """Custom manager for loan querysets."""

    def active(self):
        """Currently borrowed (not returned/cancelled)."""
        return self.filter(status=Loan.Status.BORROWED)

    def overdue(self):
        """Loans past their due date."""
        return self.filter(
            status=Loan.Status.BORROWED,
            due_date__lt=timezone.localdate(),
        )

    def by_user(self, user):
        return self.filter(user=user).select_related("book").order_by("-loan_date")

    def due_soon(self, days: int = 3):
        """Loans due within `days` days."""
        from datetime import timedelta
        limit = timezone.localdate() + timedelta(days=days)
        return self.filter(
            status=Loan.Status.BORROWED,
            due_date__lte=limit,
            due_date__gte=timezone.localdate(),
        )


class Loan(models.Model):
    """
    Represents a book loan transaction.

    Status flow:
        BORROWED → RETURNED (normal)
        BORROWED → OVERDUE (past due_date)
        BORROWED → CANCELLED (admin cancel)
    """

    class Status(models.TextChoices):
        BORROWED = "borrowed", _("Prestado")
        RETURNED = "returned", _("Devuelto")
        OVERDUE = "overdue", _("Vencido")
        CANCELLED = "cancelled", _("Cancelado")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans",
        verbose_name=_("usuario"),
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.PROTECT,
        related_name="loans",
        verbose_name=_("libro"),
    )

    # Dates
    loan_date = models.DateField(_("fecha de préstamo"), default=dt.date.today)
    due_date = models.DateField(_("fecha de vencimiento"))
    return_date = models.DateField(_("fecha de devolución"), null=True, blank=True)

    # Status & fines
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.BORROWED,
        db_index=True,
    )
    fine_amount = models.DecimalField(
        _("multa"),
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    fine_paid = models.BooleanField(_("multa pagada"), default=False)

    # Renewals
    renewal_count = models.PositiveSmallIntegerField(_("renovaciones"), default=0)

    # Notes
    notes = models.TextField(_("notas"), blank=True, max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LoanManager()

    class Meta:
        verbose_name = _("préstamo")
        verbose_name_plural = _("préstamos")
        ordering = ["-loan_date"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["book", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gte=models.F("loan_date")),
                name="loan_due_date_after_loan_date",
            )
        ]

    def __str__(self) -> str:
        return f"Préstamo: {self.book.title} → {self.user.email} ({self.status})"

    @property
    def is_overdue(self) -> bool:
        if self.status != self.Status.BORROWED:
            return False
        return timezone.localdate() > self.due_date

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        delta = timezone.localdate() - self.due_date
        return delta.days

    @property
    def days_remaining(self) -> int:
        if self.status != self.Status.BORROWED:
            return 0
        delta = self.due_date - timezone.localdate()
        return max(delta.days, 0)

    @property
    def calculated_fine(self) -> Decimal:
        """Calculate fine based on overdue days."""
        if not self.is_overdue:
            return Decimal("0.00")
        fine_per_day = Decimal(str(settings.LEXORA.get("FINE_PER_DAY", 0.50)))
        return Decimal(self.days_overdue) * fine_per_day

    def calculate_due_date(self) -> None:
        """Set due_date based on LEXORA settings."""
        from datetime import timedelta
        duration = settings.LEXORA.get("LOAN_DURATION_DAYS", 14)
        self.due_date = self.loan_date + timedelta(days=duration)

    def save(self, *args, **kwargs) -> None:
        if self._state.adding and not self.due_date:
            self.calculate_due_date()
        super().save(*args, **kwargs)
