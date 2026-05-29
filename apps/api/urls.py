"""API v1 URL configuration for Lexora Library."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views.book_views import BookViewSet, AuthorViewSet, CategoryViewSet, PublisherViewSet
from .views.loan_views import LoanViewSet
from .views.review_views import ReviewViewSet
from .views.auth_views import RegisterView, MeView, ChangePasswordView, LogoutView
from .views.dashboard_views import DashboardStatsView, PopularBooksStatsView

app_name = "api"

router = DefaultRouter()
router.register(r"books", BookViewSet, basename="book")
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"publishers", PublisherViewSet, basename="publisher")
router.register(r"loans", LoanViewSet, basename="loan")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),

    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Dashboard stats
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard_stats"),
    path("dashboard/popular-books/", PopularBooksStatsView.as_view(), name="popular_books"),
]
