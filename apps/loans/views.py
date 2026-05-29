"""Loan views for the web interface."""
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Loan
from apps.books.models import Book
from services.loan_service import LoanService
from core.exceptions import (
    BookNotAvailableError, LoanLimitExceededError,
    UserHasOverdueLoanError, LoanAlreadyReturnedError, RenewalLimitExceededError,
)


class MyLoansView(LoginRequiredMixin, ListView):
    template_name = "loans/my_loans.html"
    context_object_name = "loans"
    paginate_by = 20

    def get_queryset(self):
        return Loan.objects.filter(
            user=self.request.user
        ).select_related("book").prefetch_related("book__authors").order_by("-loan_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_loans"] = self.get_queryset().filter(status=Loan.Status.BORROWED)
        ctx["overdue_loans"] = [l for l in ctx["active_loans"] if l.is_overdue]
        return ctx


class BorrowBookView(LoginRequiredMixin, View):
    """Handle book borrow requests."""

    def post(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id, is_active=True)
        service = LoanService()
        try:
            loan = service.borrow_book(user=request.user, book=book)
            messages.success(
                request,
                f'✅ ¡Préstamo aprobado! Devuelve "{book.title}" antes del {loan.due_date.strftime("%d/%m/%Y")}.'
            )
        except (BookNotAvailableError, LoanLimitExceededError, UserHasOverdueLoanError) as e:
            messages.error(request, e.message)

        return redirect("books:detail", slug=book.slug)


class ReturnBookView(LoginRequiredMixin, View):
    """Handle book return."""

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)

        # Only owner or librarian can return
        if not (request.user == loan.user or request.user.is_librarian):
            messages.error(request, "No tienes permiso para devolver este préstamo.")
            return redirect("loans:my_loans")

        service = LoanService()
        try:
            loan = service.return_book(loan)
            msg = f'📚 "{loan.book.title}" devuelto correctamente.'
            if loan.fine_amount > 0:
                msg += f" Multa generada: ${loan.fine_amount}."
            messages.success(request, msg)
        except LoanAlreadyReturnedError as e:
            messages.error(request, e.message)

        return redirect("loans:my_loans")


class RenewLoanView(LoginRequiredMixin, View):
    """Handle loan renewal."""

    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, pk=loan_id)

        if not (request.user == loan.user or request.user.is_librarian):
            messages.error(request, "No tienes permiso para renovar este préstamo.")
            return redirect("loans:my_loans")

        service = LoanService()
        try:
            loan = service.renew_loan(loan)
            messages.success(
                request,
                f'🔄 Préstamo renovado. Nueva fecha de devolución: {loan.due_date.strftime("%d/%m/%Y")}.'
            )
        except (RenewalLimitExceededError, LoanAlreadyReturnedError) as e:
            messages.error(request, e.message)

        return redirect("loans:my_loans")
