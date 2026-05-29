"""Tests for core models: Book, Review, Notification, User."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.books.models import Book, Author, Category
from apps.loans.models import Loan
from apps.reviews.models import Review
from apps.notifications.models import Notification

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="model@lexora.com", username="modeluser",
        first_name="Model", last_name="User",
        password="Pass123!", role="member"
    )


@pytest.fixture
def book(db):
    author = Author.objects.create(full_name="Author One")
    b = Book.objects.create(
        title="Test Book", isbn="978-0-000-99001-1", stock=5, available_stock=5
    )
    b.authors.add(author)
    return b


@pytest.mark.django_db
class TestUserModel:
    def test_membership_number_auto_generated(self, user):
        assert user.membership_number.startswith("LX-")
        assert len(user.membership_number) > 3

    def test_full_name(self, user):
        assert user.full_name == "Model User"

    def test_is_librarian_for_admin(self, db):
        admin = User.objects.create_user(
            email="admin2@lexora.com", username="admin2", password="Pass!", role="admin"
        )
        assert admin.is_librarian

    def test_member_is_not_librarian(self, user):
        assert not user.is_librarian

    def test_active_loan_count(self, user, book):
        assert user.active_loan_count == 0
        Loan.objects.create(
            user=user, book=book, status=Loan.Status.BORROWED,
            loan_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        assert user.active_loan_count == 1


@pytest.mark.django_db
class TestBookModel:
    def test_is_available(self, book):
        assert book.is_available

    def test_not_available_when_no_stock(self, book):
        book.available_stock = 0
        assert not book.is_available

    def test_slug_auto_generated(self, book):
        assert book.slug != ""
        assert "test" in book.slug.lower()

    def test_availability_percentage(self, book):
        book.available_stock = 3
        book.stock = 5
        assert book.availability_percentage == 60.0

    def test_average_rating_no_reviews(self, book):
        assert book.average_rating == 0

    def test_average_rating_with_reviews(self, user, book):
        Review.objects.create(user=user, book=book, rating=4, comment="Good")
        assert book.average_rating == 4.0


@pytest.mark.django_db
class TestLoanModel:
    def _make_loan(self, user, book, days_overdue=0, status=Loan.Status.BORROWED):
        today = timezone.localdate()
        if days_overdue:
            due = today - timedelta(days=days_overdue)
            loan_date = today - timedelta(days=days_overdue + 7)
        else:
            due = today + timedelta(days=14)
            loan_date = today
        return Loan.objects.create(
            user=user, book=book, status=status,
            loan_date=loan_date,
            due_date=due,
        )

    def test_is_overdue_when_past_due(self, user, book):
        loan = self._make_loan(user, book, days_overdue=3)
        assert loan.is_overdue

    def test_not_overdue_when_current(self, user, book):
        loan = self._make_loan(user, book)
        assert not loan.is_overdue

    def test_days_overdue(self, user, book):
        loan = self._make_loan(user, book, days_overdue=5)
        assert loan.days_overdue >= 5

    def test_calculated_fine(self, user, book):
        loan = self._make_loan(user, book, days_overdue=4)
        assert loan.calculated_fine >= Decimal("2.00")

    def test_due_date_auto_set(self, user, book):
        loan = Loan.objects.create(user=user, book=book)
        assert loan.due_date is not None
        assert loan.due_date == loan.loan_date + timedelta(days=14)


@pytest.mark.django_db
class TestReviewModel:
    def test_unique_per_user_book(self, user, book):
        Review.objects.create(user=user, book=book, rating=5, comment="Great!")
        with pytest.raises(Exception):
            Review.objects.create(user=user, book=book, rating=3, comment="Also good")

    def test_star_display(self, user, book):
        review = Review(user=user, book=book, rating=3, comment="OK")
        assert review.star_display == "★★★☆☆"

    def test_approved_manager(self, user, book):
        Review.objects.create(user=user, book=book, rating=4, comment="Good", is_approved=True)
        assert Review.objects.approved().count() == 1


@pytest.mark.django_db
class TestNotificationModel:
    def test_mark_read(self, user):
        n = Notification.objects.create(
            user=user,
            type=Notification.Type.SYSTEM,
            title="Test",
            message="Hello",
        )
        assert not n.is_read
        n.mark_read()
        n.refresh_from_db()
        assert n.is_read

    def test_str_representation(self, user):
        n = Notification(
            user=user,
            type=Notification.Type.LOAN_DUE,
            title="Due soon",
            message="Book due tomorrow",
        )
        assert "loan_due" in str(n)
        assert "Due soon" in str(n)
