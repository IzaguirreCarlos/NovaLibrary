"""
Loan Service — orchestrates all business logic for book loans.

This is the single source of truth for loan operations.
All validation, stock management, and notifications flow through here.
"""
from __future__ import annotations
import logging
from django.conf import settings
from django.db import transaction
from core.exceptions import (
    BookNotAvailableError,
    LoanLimitExceededError,
    UserHasOverdueLoanError,
    LoanAlreadyReturnedError,
    RenewalLimitExceededError,
)
from repositories.book_repository import BookRepository
from repositories.loan_repository import LoanRepository
from apps.loans.models import Loan

logger = logging.getLogger("lexora.services.loan")


class LoanService:
    """Service layer for loan operations."""

    def __init__(self):
        self.book_repo = BookRepository()
        self.loan_repo = LoanRepository()

    # ─── Borrow ───────────────────────────────────────────────────────────────

    @transaction.atomic
    def borrow_book(self, user, book, notes: str = "") -> Loan:
        """
        Process a book loan request.

        Validations:
            1. Book must be available (stock > 0)
            2. User must not exceed max loan limit
            3. User must not have overdue loans
            4. User must not already have this book borrowed

        Returns:
            Loan: The created loan object

        Raises:
            BookNotAvailableError, LoanLimitExceededError,
            UserHasOverdueLoanError
        """
        logger.info("Loan request: user=%s, book=%s", user.email, book.isbn)

        # 1. Check book availability
        if not book.is_available:
            raise BookNotAvailableError(book.title)

        # 2. Check loan limit
        max_loans = settings.LEXORA["MAX_LOANS_PER_USER"]
        active_count = LoanRepository.count_active_by_user(user)
        if active_count >= max_loans:
            raise LoanLimitExceededError(max_loans)

        # 3. Check for overdue loans
        if LoanRepository.user_has_overdue(user):
            raise UserHasOverdueLoanError()

        # 4. Check if user already has this book
        if LoanRepository.user_already_has_book(user, book):
            raise BookNotAvailableError(f"{book.title} (ya lo tienes prestado)")

        # Create loan — signal will handle stock decrement
        loan = LoanRepository.create(user=user, book=book, notes=notes)

        logger.info("Loan created: %s (due: %s)", loan.pk, loan.due_date)
        return loan

    # ─── Return ───────────────────────────────────────────────────────────────

    @transaction.atomic
    def return_book(self, loan: Loan) -> Loan:
        """
        Process a book return.

        Raises:
            LoanAlreadyReturnedError
        """
        if loan.status == Loan.Status.RETURNED:
            raise LoanAlreadyReturnedError()

        if loan.status == Loan.Status.CANCELLED:
            raise LoanAlreadyReturnedError()

        # Mark as returned and calculate fine
        loan = LoanRepository.mark_returned(loan)

        # Restore stock
        BookRepository.increment_available_stock(loan.book)

        # Notify user
        self._notify_return(loan)

        logger.info("Book returned: loan=%s, fine=$%.2f", loan.pk, loan.fine_amount)
        return loan

    # ─── Renew ────────────────────────────────────────────────────────────────

    @transaction.atomic
    def renew_loan(self, loan: Loan) -> Loan:
        """
        Renew a loan by extending the due date.

        Raises:
            RenewalLimitExceededError
            LoanAlreadyReturnedError (if not active)
        """
        if loan.status != Loan.Status.BORROWED:
            raise LoanAlreadyReturnedError()

        max_renewals = settings.LEXORA["RENEWAL_LIMIT"]
        if loan.renewal_count >= max_renewals:
            raise RenewalLimitExceededError(max_renewals)

        duration = settings.LEXORA["LOAN_DURATION_DAYS"]
        loan = LoanRepository.renew(loan, days=duration)

        logger.info("Loan renewed: %s (new due: %s)", loan.pk, loan.due_date)
        return loan

    # ─── Overdue Processing ───────────────────────────────────────────────────

    def process_overdue_loans(self) -> int:
        """
        Mark overdue loans and send notifications. Called by Celery beat.
        Returns number of loans marked overdue.
        """
        overdue_loans = LoanRepository.get_all_overdue()
        count = 0
        for loan in overdue_loans:
            if loan.status == Loan.Status.BORROWED:
                loan.status = Loan.Status.OVERDUE
                loan.fine_amount = loan.calculated_fine
                loan.save(update_fields=["status", "fine_amount"])
                self._notify_overdue(loan)
                count += 1

        logger.info("Processed %d overdue loans", count)
        return count

    def send_due_reminders(self, days_before: int = 3) -> int:
        """Send reminder emails for loans due soon."""
        loans = LoanRepository.get_due_soon(days=days_before)
        count = 0
        for loan in loans:
            self._notify_due_soon(loan, days_before)
            count += 1
        logger.info("Sent %d due-soon reminders (%d days)", count, days_before)
        return count

    # ─── Private Notifications ────────────────────────────────────────────────

    @staticmethod
    def _notify_return(loan: Loan) -> None:
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=loan.user,
            type=Notification.Type.LOAN_RETURNED,
            title="Devolución confirmada",
            message=f'Has devuelto "{loan.book.title}" correctamente.'
                    + (f" Multa generada: ${loan.fine_amount}" if loan.fine_amount > 0 else ""),
            loan_id=loan.pk,
            book_id=loan.book.pk,
        )

    @staticmethod
    def _notify_overdue(loan: Loan) -> None:
        from apps.notifications.models import Notification
        Notification.objects.get_or_create(
            loan_id=loan.pk,
            type=Notification.Type.LOAN_OVERDUE,
            defaults={
                "user": loan.user,
                "title": "Préstamo vencido",
                "message": f'Tu préstamo de "{loan.book.title}" venció el {loan.due_date}. '
                           f'Multa actual: ${loan.calculated_fine}.',
                "book_id": loan.book.pk,
            },
        )

    @staticmethod
    def _notify_due_soon(loan: Loan, days: int) -> None:
        from apps.notifications.models import Notification
        Notification.objects.get_or_create(
            loan_id=loan.pk,
            type=Notification.Type.LOAN_DUE,
            defaults={
                "user": loan.user,
                "title": f"Vencimiento en {days} días",
                "message": f'Tu préstamo de "{loan.book.title}" vence el {loan.due_date}. '
                           f'Por favor, devuélvelo o renuévalo.',
                "book_id": loan.book.pk,
            },
        )
