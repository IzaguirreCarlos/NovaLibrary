"""Loan URL patterns."""
from django.urls import path
from .views import MyLoansView, BorrowBookView, ReturnBookView, RenewLoanView

app_name = "loans"

urlpatterns = [
    path("", MyLoansView.as_view(), name="my_loans"),
    path("borrow/<uuid:book_id>/", BorrowBookView.as_view(), name="borrow"),
    path("return/<uuid:loan_id>/", ReturnBookView.as_view(), name="return"),
    path("renew/<uuid:loan_id>/", RenewLoanView.as_view(), name="renew"),
]
