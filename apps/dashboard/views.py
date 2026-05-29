"""Dashboard views."""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from core.mixins import LibrarianRequiredMixin
from apps.loans.models import Loan
from apps.books.models import Book
from repositories.loan_repository import LoanRepository
from repositories.book_repository import BookRepository


class HomeView(LoginRequiredMixin, TemplateView):
    """Landing dashboard — adapts to user role."""

    def get_template_names(self):
        user = self.request.user
        if user.is_librarian:
            return ["dashboard/admin_dashboard.html"]
        return ["dashboard/member_dashboard.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_librarian:
            ctx.update(self._get_admin_context())
        else:
            ctx.update(self._get_member_context(user))

        return ctx

    def _get_admin_context(self) -> dict:
        from apps.accounts.models import User
        loan_stats = LoanRepository.get_dashboard_stats()
        return {
            "loan_stats": loan_stats,
            "recent_loans": Loan.objects.select_related("user", "book").order_by("-created_at")[:10],
            "overdue_loans": Loan.objects.filter(
                status=Loan.Status.BORROWED,
                due_date__lt=timezone.now().date()
            ).select_related("user", "book")[:10],
            "popular_books": BookRepository.get_popular(limit=5),
            "top_rated_books": BookRepository.get_top_rated(limit=5),
            "total_books": Book.objects.filter(is_active=True).count(),
            "total_users": User.objects.filter(is_active=True).count(),
            "books_out_of_stock": Book.objects.filter(is_active=True, available_stock=0).count(),
        }

    def _get_member_context(self, user) -> dict:
        from repositories.loan_repository import LoanRepository
        active_loans = LoanRepository.get_active_by_user(user)
        return {
            "active_loans": active_loans,
            "overdue_loans": [l for l in active_loans if l.is_overdue],
            "loan_history": LoanRepository.get_all_by_user(user)[:5],
            "featured_books": BookRepository.get_featured()[:8],
            "popular_books": BookRepository.get_popular(limit=6),
        }


class DashboardView(LibrarianRequiredMixin, TemplateView):
    """Full admin dashboard with analytics."""
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Chart data for loans over last 30 days
        from datetime import timedelta
        from django.db.models.functions import TruncDate
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        loans_by_day = (
            Loan.objects
            .filter(loan_date__gte=thirty_days_ago)
            .annotate(day=TruncDate("loan_date"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        ctx["loans_chart_data"] = list(loans_by_day)

        # Books by category
        from apps.books.models import Category
        books_by_category = (
            Category.objects
            .annotate(book_count=Count("books"))
            .filter(book_count__gt=0)
            .values("name", "color", "book_count")
            .order_by("-book_count")[:10]
        )
        ctx["category_chart_data"] = list(books_by_category)
        return ctx
