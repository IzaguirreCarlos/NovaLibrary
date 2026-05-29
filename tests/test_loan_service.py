"""
Unit tests for LoanService.

Tests the full business logic layer without touching the API.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.books.models import Book, Author, Category
from apps.loans.models import Loan
from services.loan_service import LoanService
from core.exceptions import (
    BookNotAvailableError, LoanLimitExceededError,
    UserHasOverdueLoanError, LoanAlreadyReturnedError,
)

User = get_user_model()


@pytest.mark.django_db
class TestLoanService(TestCase):
    """Test suite for LoanService business logic."""

    def setUp(self):
        self.service = LoanService()
        self.user = User.objects.create_user(
            email="test@lexora.com",
            username="testuser",
            password="TestPass123!",
            role="member",
        )
        self.author = Author.objects.create(full_name="Test Author")
        self.category = Category.objects.create(name="Test Category", color="#6366f1")
        self.book = Book.objects.create(
            title="Test Book",
            isbn="978-0-000-00001-1",
            stock=3,
            available_stock=3,
        )
        self.book.authors.add(self.author)
        self.book.categories.add(self.category)

    def test_borrow_book_success(self):
        """Should create a loan when book is available."""
        loan = self.service.borrow_book(self.user, self.book)
        assert loan.status == Loan.Status.BORROWED
        assert loan.user == self.user
        assert loan.book == self.book
        assert loan.due_date is not None

    def test_borrow_unavailable_book_raises(self):
        """Should raise BookNotAvailableError when stock is 0."""
        self.book.available_stock = 0
        self.book.save()
        with pytest.raises(BookNotAvailableError):
            self.service.borrow_book(self.user, self.book)

    def test_borrow_over_limit_raises(self):
        """Should raise LoanLimitExceededError when max loans reached."""
        # Create max active loans (5)
        from datetime import date, timedelta
        for i in range(5):
            book = Book.objects.create(
                title=f"Book {i}", isbn=f"978-0-000-000{i+2}-1",
                stock=1, available_stock=1
            )
            Loan.objects.create(
                user=self.user, book=book, status=Loan.Status.BORROWED,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=14),
            )
        with pytest.raises(LoanLimitExceededError):
            self.service.borrow_book(self.user, self.book)

    def test_return_book_success(self):
        """Should mark loan as returned and set return date."""
        from datetime import timedelta
        today = timezone.localdate()
        loan = Loan.objects.create(
            user=self.user, book=self.book, status=Loan.Status.BORROWED,
            loan_date=today,
            due_date=today + timedelta(days=14),
        )
        returned = self.service.return_book(loan)
        assert returned.status == Loan.Status.RETURNED
        assert returned.return_date == today

    def test_return_already_returned_raises(self):
        """Should raise LoanAlreadyReturnedError if loan is already returned."""
        from datetime import date, timedelta
        loan = Loan.objects.create(
            user=self.user, book=self.book, status=Loan.Status.RETURNED,
            loan_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=3),
            return_date=date.today() - timedelta(days=5),
        )
        with pytest.raises(LoanAlreadyReturnedError):
            self.service.return_book(loan)

    def test_overdue_fine_calculation(self):
        """Should correctly calculate fine for overdue loans."""
        from datetime import timedelta
        today = timezone.localdate()
        loan = Loan(
            user=self.user,
            book=self.book,
            status=Loan.Status.BORROWED,
            loan_date=today - timedelta(days=20),
            due_date=today - timedelta(days=5),  # 5 days overdue
        )
        assert loan.days_overdue == 5
        assert loan.calculated_fine == Decimal("2.50")  # 5 * 0.50
