"""Tests for the loans API endpoints."""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.books.models import Book, Author
from apps.loans.models import Loan

User = get_user_model()


def make_book(isbn, stock=3):
    author = Author.objects.create(full_name="Author " + isbn[-1])
    book = Book.objects.create(
        title=f"Book {isbn}", isbn=isbn, stock=stock, available_stock=stock
    )
    book.authors.add(author)
    return book


def get_token(client, email, password):
    resp = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    return resp.json()["access"]


@pytest.fixture
def member(db):
    return User.objects.create_user(
        email="loanmember@lexora.com", username="loanmember", password="Pass123!", role="member"
    )


@pytest.fixture
def librarian(db):
    return User.objects.create_user(
        email="loanlib@lexora.com", username="loanlib", password="Pass123!", role="librarian"
    )


@pytest.mark.django_db
class TestLoanCreateAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_borrow_book_success(self, member):
        book = make_book("978-1-000-00001-1")
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/loans/", {"book_id": str(book.pk)}, format="json")
        assert response.status_code == 201
        assert response.json()["status"] == "success"
        book.refresh_from_db()
        assert book.available_stock == 2

    def test_borrow_unavailable_book(self, member):
        book = make_book("978-1-000-00002-1", stock=0)
        book.available_stock = 0
        book.save()
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/loans/", {"book_id": str(book.pk)}, format="json")
        assert response.status_code == 422
        assert response.json()["code"] == "book_not_available"

    def test_borrow_nonexistent_book(self, member):
        import uuid
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/loans/", {"book_id": str(uuid.uuid4())}, format="json")
        assert response.status_code == 404


@pytest.mark.django_db
class TestLoanReturnAPI:
    def setup_method(self):
        self.client = APIClient()

    def _create_loan(self, user, book):
        return Loan.objects.create(
            user=user, book=book, status=Loan.Status.BORROWED,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )

    def test_return_book_success(self, member):
        book = make_book("978-1-000-00003-1")
        loan = self._create_loan(member, book)
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/v1/loans/{loan.pk}/return_book/")
        assert response.status_code == 200
        loan.refresh_from_db()
        assert loan.status == Loan.Status.RETURNED

    def test_return_already_returned(self, member):
        book = make_book("978-1-000-00004-1")
        loan = Loan.objects.create(
            user=member, book=book, status=Loan.Status.RETURNED,
            loan_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=3),
            return_date=date.today() - timedelta(days=5),
        )
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/v1/loans/{loan.pk}/return_book/")
        assert response.status_code == 422
        assert response.json()["code"] == "loan_already_returned"


@pytest.mark.django_db
class TestLoanRenewAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_renew_loan_success(self, member):
        book = make_book("978-1-000-00005-1")
        original_due = date.today() + timedelta(days=7)
        loan = Loan.objects.create(
            user=member, book=book, status=Loan.Status.BORROWED,
            loan_date=date.today(), due_date=original_due,
        )
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/v1/loans/{loan.pk}/renew/")
        assert response.status_code == 200
        loan.refresh_from_db()
        assert loan.renewal_count == 1
        assert loan.due_date > original_due

    def test_renew_exceeds_limit(self, member):
        book = make_book("978-1-000-00006-1")
        loan = Loan.objects.create(
            user=member, book=book, status=Loan.Status.BORROWED,
            loan_date=date.today(), due_date=date.today() + timedelta(days=14),
            renewal_count=2,
        )
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/v1/loans/{loan.pk}/renew/")
        assert response.status_code == 422
        assert response.json()["code"] == "renewal_limit_exceeded"


@pytest.mark.django_db
class TestOverdueEndpoint:
    def setup_method(self):
        self.client = APIClient()

    def test_overdue_requires_librarian(self, member):
        token = get_token(self.client, "loanmember@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/loans/overdue/")
        assert response.status_code == 403

    def test_overdue_accessible_by_librarian(self, librarian):
        token = get_token(self.client, "loanlib@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/loans/overdue/")
        assert response.status_code == 200
