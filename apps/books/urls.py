"""Book URL patterns."""
from django.urls import path
from .views import BookListView, BookDetailView, AuthorDetailView

app_name = "books"

urlpatterns = [
    path("", BookListView.as_view(), name="list"),
    path("<slug:slug>/", BookDetailView.as_view(), name="detail"),
    path("author/<slug:slug>/", AuthorDetailView.as_view(), name="author_detail"),
]
