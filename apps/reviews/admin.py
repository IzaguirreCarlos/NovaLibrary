"""Admin configuration for reviews app."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book_title", "user_email", "rating_stars", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    search_fields = ("book__title", "user__email", "comment")
    list_editable = ("is_approved",)
    readonly_fields = ("created_at", "updated_at")

    def book_title(self, obj):
        return obj.book.title[:40]
    book_title.short_description = "Libro"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Usuario"

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Calificación"
