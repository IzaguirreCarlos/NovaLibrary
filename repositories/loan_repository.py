"""Loan Repository — data access layer for loans."""
from __future__ import annotations
from typing import Optional
from django.db.models import QuerySet, Sum
from django.utils import timezone
from apps.loans.models import Loan


class LoanRepository:
    """All database operations for the Loan model."""

    @staticmethod
    def get_by_id(loan_id) -> Optional[Loan]:
        try:
            return Loan.objects.select_related("user", "book").get(pk=loan_id)
        except Loan.DoesNotExist:
            return None

    @staticmethod
    def get_active_by_user(user) -> QuerySet:
        return (
            Loan.objects
            .filter(user=user, status=Loan.Status.BORROWED)
            .select_related("book")
            .prefetch_related("book__authors")
            .order_by("due_date")
        )

    @staticmethod
    def get_all_by_user(user) -> QuerySet:
        return (
            Loan.objects
            .filter(user=user)
            .select_related("book")
            .prefetch_related("book__authors")
            .order_by("-loan_date")
        )

    @staticmethod
    def get_all_overdue() -> QuerySet:
        return (
            Loan.objects
            .filter(status=Loan.Status.BORROWED, due_date__lt=timezone.localdate())
            .select_related("user", "book")
            .order_by("due_date")
        )

    @staticmethod
    def get_due_soon(days: int = 3) -> QuerySet:
        from datetime import timedelta
        limit = timezone.localdate() + timedelta(days=days)
        return (
            Loan.objects
            .filter(
                status=Loan.Status.BORROWED,
                due_date__lte=limit,
                due_date__gte=timezone.localdate(),
            )
            .select_related("user", "book")
        )

    @staticmethod
    def count_active_by_user(user) -> int:
        return Loan.objects.filter(user=user, status=Loan.Status.BORROWED).count()

    @staticmethod
    def user_has_overdue(user) -> bool:
        return Loan.objects.filter(
            user=user,
            status=Loan.Status.BORROWED,
            due_date__lt=timezone.localdate(),
        ).exists()

    @staticmethod
    def user_already_has_book(user, book) -> bool:
        return Loan.objects.filter(user=user, book=book, status=Loan.Status.BORROWED).exists()

    @staticmethod
    def create(user, book, notes: str = "") -> Loan:
        return Loan.objects.create(user=user, book=book, notes=notes)

    @staticmethod
    def mark_returned(loan: Loan) -> Loan:
        from decimal import Decimal
        loan.status = Loan.Status.RETURNED
        loan.return_date = timezone.localdate()
        loan.fine_amount = loan.calculated_fine
        loan.save(update_fields=["status", "return_date", "fine_amount", "updated_at"])
        return loan

    @staticmethod
    def mark_overdue_bulk() -> int:
        """Mark all past-due borrowed loans as overdue. Returns count."""
        count, _ = Loan.objects.filter(
            status=Loan.Status.BORROWED,
            due_date__lt=timezone.localdate(),
        ).update(status=Loan.Status.OVERDUE)
        return count

    @staticmethod
    def renew(loan: Loan, days: int = 14) -> Loan:
        from datetime import timedelta
        loan.due_date = loan.due_date + timedelta(days=days)
        loan.renewal_count += 1
        loan.save(update_fields=["due_date", "renewal_count", "updated_at"])
        return loan

    @staticmethod
    def get_dashboard_stats() -> dict:
        from django.db.models import Count
        return {
            "total_loans": Loan.objects.count(),
            "active_loans": Loan.objects.filter(status=Loan.Status.BORROWED).count(),
            "overdue_loans": Loan.objects.filter(
                status=Loan.Status.BORROWED,
                due_date__lt=timezone.localdate()
            ).count(),
            "returned_loans": Loan.objects.filter(status=Loan.Status.RETURNED).count(),
            "total_fines": Loan.objects.aggregate(total=Sum("fine_amount"))["total"] or 0,
        }
