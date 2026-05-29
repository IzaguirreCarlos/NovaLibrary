"""Reviews URL patterns."""
from django.urls import path
from .views import CreateReviewView, DeleteReviewView, EditReviewView

app_name = "reviews"

urlpatterns = [
    path("create/<uuid:book_id>/", CreateReviewView.as_view(), name="create"),
    path("delete/<uuid:review_id>/", DeleteReviewView.as_view(), name="delete"),
    path("edit/<uuid:review_id>/", EditReviewView.as_view(), name="edit"),
]
