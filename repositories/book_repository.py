"""
Book Repository — data access layer for books.

Encapsulates all DB queries related to books, keeping services clean.
"""
from __future__ import annotations
import logging
from typing import Optional
from django.core.cache import cache
from django.db.models import QuerySet, Count, Avg
from django.conf import settings
from apps.books.models import Book, Author, Category, Publisher

logger = logging.getLogger("lexora.repositories")


class BookRepository:
    """All database operations for the Book model."""

    # ─── Read ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(book_id) -> Optional[Book]:
        cache_key = f"book_detail_{book_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        try:
            book = (
                Book.objects
                .select_related("publisher")
                .prefetch_related("authors", "categories")
                .get(pk=book_id, is_active=True)
            )
            cache.set(cache_key, book, settings.LEXORA["CACHE_BOOK_DETAIL_TIMEOUT"])
            return book
        except Book.DoesNotExist:
            return None

    @staticmethod
    def get_by_isbn(isbn: str) -> Optional[Book]:
        try:
            return Book.objects.select_related("publisher").prefetch_related("authors", "categories").get(isbn=isbn)
        except Book.DoesNotExist:
            return None

    @staticmethod
    def get_all_active() -> QuerySet:
        return (
            Book.objects
            .filter(is_active=True)
            .select_related("publisher")
            .prefetch_related("authors", "categories")
            .annotate(avg_rating=Avg("reviews__rating"), loan_count=Count("loans"))
            .order_by("-created_at")
        )

    @staticmethod
    def get_available() -> QuerySet:
        return BookRepository.get_all_active().filter(available_stock__gt=0)

    @staticmethod
    def get_featured() -> QuerySet:
        cache_key = "book_list_featured"
        cached = cache.get(cache_key)
        if cached:
            return cached
        qs = (
            Book.objects
            .filter(is_featured=True, is_active=True)
            .select_related("publisher")
            .prefetch_related("authors", "categories")
            [:12]
        )
        # Force evaluation for caching
        featured = list(qs)
        cache.set(cache_key, featured, settings.LEXORA["CACHE_BOOK_LIST_TIMEOUT"])
        return featured

    @staticmethod
    def get_popular(limit: int = 10) -> QuerySet:
        return (
            Book.objects
            .filter(is_active=True)
            .annotate(loan_count=Count("loans"))
            .order_by("-loan_count")
            .select_related("publisher")
            .prefetch_related("authors")
            [:limit]
        )

    @staticmethod
    def get_top_rated(limit: int = 10) -> QuerySet:
        return (
            Book.objects
            .filter(is_active=True)
            .annotate(avg_rating=Avg("reviews__rating"))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating")
            .select_related("publisher")
            .prefetch_related("authors")
            [:limit]
        )

    @staticmethod
    def search(query: str, category_slug: str = "", language: str = "") -> QuerySet:
        qs = Book.objects.filter(is_active=True).select_related("publisher").prefetch_related("authors", "categories")

        if query:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(authors__full_name__icontains=query)
                | Q(isbn__icontains=query)
                | Q(publisher__name__icontains=query)
                | Q(categories__name__icontains=query)
                | Q(description__icontains=query)
            ).distinct()

        if category_slug:
            qs = qs.filter(categories__slug=category_slug)

        if language:
            qs = qs.filter(language=language)

        return qs.annotate(avg_rating=Avg("reviews__rating"), loan_count=Count("loans"))

    # ─── Write ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(data: dict) -> Book:
        authors = data.pop("authors", [])
        categories = data.pop("categories", [])
        book = Book.objects.create(**data)
        if authors:
            book.authors.set(authors)
        if categories:
            book.categories.set(categories)
        logger.info("Book created: %s (ISBN: %s)", book.title, book.isbn)
        return book

    @staticmethod
    def update(book: Book, data: dict) -> Book:
        authors = data.pop("authors", None)
        categories = data.pop("categories", None)
        for field, value in data.items():
            setattr(book, field, value)
        book.save()
        if authors is not None:
            book.authors.set(authors)
        if categories is not None:
            book.categories.set(categories)
        logger.info("Book updated: %s", book.title)
        return book

    @staticmethod
    def delete(book: Book) -> None:
        book.is_active = False
        book.save(update_fields=["is_active"])
        logger.info("Book soft-deleted: %s", book.title)

    @staticmethod
    def increment_stock(book: Book, amount: int = 1) -> None:
        from django.db.models import F
        Book.objects.filter(pk=book.pk).update(
            stock=F("stock") + amount,
            available_stock=F("available_stock") + amount,
        )

    @staticmethod
    def decrement_available_stock(book: Book) -> None:
        from django.db.models import F
        Book.objects.filter(pk=book.pk).update(
            available_stock=F("available_stock") - 1
        )

    @staticmethod
    def increment_available_stock(book: Book) -> None:
        from django.db.models import F
        Book.objects.filter(pk=book.pk).update(
            available_stock=F("available_stock") + 1
        )
