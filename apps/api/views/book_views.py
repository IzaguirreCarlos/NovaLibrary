"""API ViewSets for books, authors, categories and publishers."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as drf_filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.books.models import Book, Author, Category, Publisher
from apps.api.serializers import (
    BookListSerializer, BookDetailSerializer,
    AuthorSerializer, CategorySerializer, PublisherSerializer,
)
from permissions.api_permissions import ReadOnlyOrLibrarian
from repositories.book_repository import BookRepository


class BookFilter(drf_filters.FilterSet):
    min_pages = drf_filters.NumberFilter(field_name="pages", lookup_expr="gte")
    max_pages = drf_filters.NumberFilter(field_name="pages", lookup_expr="lte")
    available = drf_filters.BooleanFilter(method="filter_available")
    category = drf_filters.CharFilter(field_name="categories__slug")
    author = drf_filters.CharFilter(field_name="authors__slug")
    publisher = drf_filters.CharFilter(field_name="publisher__slug")
    pub_year = drf_filters.NumberFilter(field_name="publication_date__year")

    class Meta:
        model = Book
        fields = ["language", "is_featured", "is_active"]

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(available_stock__gt=0)
        return queryset


@extend_schema(tags=["books"])
class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD for books catalog.

    - GET /books/ — list with filters, search, ordering
    - GET /books/{id}/ — detail
    - POST /books/ — create (librarian+)
    - PATCH /books/{id}/ — update (librarian+)
    - DELETE /books/{id}/ — soft delete (librarian+)
    - GET /books/featured/ — featured books
    - GET /books/popular/ — most borrowed
    - GET /books/top-rated/ — highest rated
    """
    queryset = Book.objects.filter(is_active=True)
    permission_classes = [ReadOnlyOrLibrarian]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "isbn", "authors__full_name", "publisher__name", "categories__name"]
    ordering_fields = ["title", "created_at", "available_stock", "publication_date"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookDetailSerializer

    def get_queryset(self):
        return BookRepository.get_all_active()

    @extend_schema(summary="Libros destacados")
    @action(detail=False, methods=["get"])
    def featured(self, request):
        books = BookRepository.get_featured()
        serializer = BookListSerializer(books, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})

    @extend_schema(summary="Libros más prestados")
    @action(detail=False, methods=["get"])
    def popular(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 50)
        books = BookRepository.get_popular(limit=limit)
        serializer = BookListSerializer(books, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})

    @extend_schema(summary="Libros mejor valorados")
    @action(detail=False, methods=["get"])
    def top_rated(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 50)
        books = BookRepository.get_top_rated(limit=limit)
        serializer = BookListSerializer(books, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})

    def destroy(self, request, *args, **kwargs):
        book = self.get_object()
        BookRepository.delete(book)
        return Response(
            {"status": "success", "message": "Libro desactivado correctamente."},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["authors"])
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [ReadOnlyOrLibrarian]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "nationality"]
    ordering_fields = ["full_name", "created_at"]
    ordering = ["full_name"]


@extend_schema(tags=["books"])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(parent=None)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


@extend_schema(tags=["books"])
class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [ReadOnlyOrLibrarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "country"]
