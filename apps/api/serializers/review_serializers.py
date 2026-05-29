"""Serializers for reviews."""
from rest_framework import serializers
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.ImageField(source="user.avatar", read_only=True)
    star_display = serializers.CharField(read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "user_name", "user_avatar", "book_title",
            "rating", "title", "comment", "star_display",
            "is_approved", "helpful_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_approved", "helpful_count", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["book", "rating", "title", "comment"]

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La calificación debe ser entre 1 y 5.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        book = attrs["book"]
        if Review.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError("Ya has escrito una reseña para este libro.")
        return attrs

    def create(self, validated_data):
        return Review.objects.create(user=self.context["request"].user, **validated_data)
