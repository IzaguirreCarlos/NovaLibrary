"""Tests for the books API endpoints."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.books.models import Book, Author, Category, Publisher

User = get_user_model()


def make_book(title="Test Book", isbn="978-0-000-00010-1", stock=3):
    author, _ = Author.objects.get_or_create(full_name=f"Author for {isbn}")
    book = Book.objects.create(title=title, isbn=isbn, stock=stock, available_stock=stock)
    book.authors.add(author)
    return book


@pytest.fixture
def member(db):
    return User.objects.create_user(
        email="member@lexora.com", username="member", password="Pass123!", role="member"
    )


@pytest.fixture
def librarian(db):
    return User.objects.create_user(
        email="lib@lexora.com", username="librarian", password="Pass123!", role="librarian"
    )


def get_token(client, email, password):
    resp = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    return resp.json()["access"]


@pytest.mark.django_db
class TestBookListAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_list_requires_auth(self):
        response = self.client.get("/api/v1/books/")
        assert response.status_code == 401

    def test_list_returns_books(self, member):
        make_book("Book A", "978-0-000-00011-1")
        make_book("Book B", "978-0-000-00012-1")
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/books/")
        assert response.status_code == 200
        assert response.json()["pagination"]["count"] >= 2

    def test_search_by_title(self, member):
        make_book("Unique Lexora Title", "978-0-000-00013-1")
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/books/?search=Unique+Lexora+Title")
        assert response.status_code == 200
        results = response.json()["results"]
        assert any("Unique Lexora Title" in b["title"] for b in results)

    def test_featured_endpoint(self, member):
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/books/featured/")
        assert response.status_code == 200
        assert "results" in response.json()

    def test_popular_endpoint(self, member):
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/books/popular/")
        assert response.status_code == 200

    def test_top_rated_endpoint(self, member):
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/books/top_rated/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestBookDetailAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_book_detail(self, member):
        book = make_book("Detail Book", "978-0-000-00014-1")
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(f"/api/v1/books/{book.pk}/")
        assert response.status_code == 200
        assert response.json()["title"] == "Detail Book"

    def test_create_book_requires_librarian(self, member):
        token = get_token(self.client, "member@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/books/", {"title": "New", "isbn": "111"}, format="json")
        assert response.status_code == 403

    def test_create_book_as_librarian(self, librarian):
        author = Author.objects.create(full_name="Author X")
        token = get_token(self.client, "lib@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "title": "Librarian Created",
            "isbn": "978-0-000-00015-1",
            "stock": 5,
            "author_ids": [str(author.pk)],
        }
        response = self.client.post("/api/v1/books/", payload, format="json")
        assert response.status_code == 201
        assert Book.objects.filter(title="Librarian Created").exists()

    def test_soft_delete_as_librarian(self, librarian):
        book = make_book("To Delete", "978-0-000-00016-1")
        token = get_token(self.client, "lib@lexora.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.delete(f"/api/v1/books/{book.pk}/")
        assert response.status_code == 200
        book.refresh_from_db()
        assert not book.is_active
