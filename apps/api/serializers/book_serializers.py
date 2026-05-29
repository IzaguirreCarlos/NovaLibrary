"""Serializers for books, authors, categories and publishers."""
from rest_framework import serializers
from apps.books.models import Book, Author, Category, Publisher


class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Author
        fields = [
            "id", "full_name", "slug", "biography", "birth_date",
            "nationality", "profile_image", "website", "book_count", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class AuthorMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "full_name", "slug", "profile_image", "nationality"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "color", "parent"]
        read_only_fields = ["id", "slug"]


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "slug", "country", "website"]
        read_only_fields = ["id", "slug"]


class BookListSerializer(serializers.ModelSerializer):
    """Compact serializer for book lists."""
    authors = AuthorMinimalSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    publisher_name = serializers.CharField(source="publisher.name", read_only=True, default="")
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id", "title", "slug", "isbn", "cover_image", "language",
            "available_stock", "is_available", "is_featured",
            "authors", "categories", "publisher_name",
            "average_rating", "review_count", "created_at",
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """Full serializer for book detail view."""
    authors = AuthorMinimalSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    availability_percentage = serializers.FloatField(read_only=True)

    # Write-only FKs
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Author.objects.all(), write_only=True, source="authors", required=False
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), write_only=True, source="categories", required=False
    )
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), write_only=True, source="publisher", required=False
    )

    class Meta:
        model = Book
        fields = [
            "id", "title", "slug", "subtitle", "isbn", "description",
            "publication_date", "language", "pages", "edition",
            "cover_image", "stock", "available_stock",
            "is_active", "is_featured", "is_available", "availability_percentage",
            "authors", "categories", "publisher",
            "author_ids", "category_ids", "publisher_id",
            "average_rating", "review_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "available_stock"]

    def create(self, validated_data):
        authors = validated_data.pop("authors", [])
        categories = validated_data.pop("categories", [])
        book = Book.objects.create(**validated_data)
        book.authors.set(authors)
        book.categories.set(categories)
        return book

    def update(self, instance, validated_data):
        authors = validated_data.pop("authors", None)
        categories = validated_data.pop("categories", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if authors is not None:
            instance.authors.set(authors)
        if categories is not None:
            instance.categories.set(categories)
        return instance
