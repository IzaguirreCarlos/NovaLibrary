"""Dashboard statistics API."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.core.cache import cache
from django.db.models import Count, Avg, Sum
from permissions.api_permissions import IsLibrarian
from repositories.loan_repository import LoanRepository


@extend_schema(tags=["dashboard"])
class DashboardStatsView(APIView):
    """Admin/Librarian dashboard statistics."""
    permission_classes = [IsLibrarian]

    def get(self, request):
        cache_key = "dashboard_stats"
        stats = cache.get(cache_key)

        if not stats:
            from apps.books.models import Book
            from apps.accounts.models import User
            from apps.loans.models import Loan
            from apps.reviews.models import Review
            from django.utils import timezone

            loan_stats = LoanRepository.get_dashboard_stats()

            stats = {
                "books": {
                    "total": Book.objects.filter(is_active=True).count(),
                    "available": Book.objects.filter(is_active=True, available_stock__gt=0).count(),
                    "out_of_stock": Book.objects.filter(is_active=True, available_stock=0).count(),
                },
                "users": {
                    "total": User.objects.filter(is_active=True).count(),
                    "members": User.objects.filter(role="member", is_active=True).count(),
                    "librarians": User.objects.filter(role="librarian", is_active=True).count(),
                },
                "loans": loan_stats,
                "reviews": {
                    "total": Review.objects.count(),
                    "average_rating": Review.objects.aggregate(avg=Avg("rating"))["avg"] or 0,
                },
            }
            cache.set(cache_key, stats, 300)

        return Response({"status": "success", "data": stats})


@extend_schema(tags=["dashboard"])
class PopularBooksStatsView(APIView):
    """Most popular books by loan count."""
    permission_classes = [IsLibrarian]

    def get(self, request):
        from apps.books.models import Book
        from apps.api.serializers import BookListSerializer

        limit = min(int(request.query_params.get("limit", 10)), 50)
        books = (
            Book.objects
            .filter(is_active=True)
            .annotate(loan_count=Count("loans"))
            .order_by("-loan_count")
            .select_related("publisher")
            .prefetch_related("authors")
            [:limit]
        )
        serializer = BookListSerializer(books, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})
