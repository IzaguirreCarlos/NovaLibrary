"""Admin configuration for books app."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Book, Author, Publisher, Category


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "nationality", "book_count", "created_at")
    search_fields = ("full_name", "nationality")
    list_filter = ("nationality",)
    prepopulated_fields = {"slug": ("full_name",)}
    readonly_fields = ("created_at",)

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = "Libros"


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "created_at")
    search_fields = ("name", "country")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "color_badge", "parent", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def color_badge(self, obj):
        return format_html(
            '<span style="background:{}; padding:2px 8px; border-radius:4px; color:white">{}</span>',
            obj.color, obj.color
        )
    color_badge.short_description = "Color"


class BookAuthorInline(admin.TabularInline):
    model = Book.authors.through
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title", "isbn", "available_stock", "stock",
        "is_available_badge", "is_featured", "language", "updated_at"
    )
    list_filter = ("is_active", "is_featured", "language", "categories")
    search_fields = ("title", "isbn", "authors__full_name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("authors", "categories")
    readonly_fields = ("created_at", "updated_at", "average_rating", "review_count")
    list_editable = ("is_featured",)

    fieldsets = (
        ("Información bibliográfica", {
            "fields": ("title", "slug", "subtitle", "isbn", "description",
                       "publication_date", "language", "pages", "edition")
        }),
        ("Relaciones", {
            "fields": ("authors", "publisher", "categories")
        }),
        ("Portada", {
            "fields": ("cover_image",)
        }),
        ("Inventario", {
            "fields": ("stock", "available_stock", "is_active", "is_featured")
        }),
        ("Estadísticas", {
            "fields": ("average_rating", "review_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def is_available_badge(self, obj):
        color = "green" if obj.is_available else "red"
        text = "Disponible" if obj.is_available else "No disponible"
        return format_html('<span style="color:{}">{}</span>', color, text)
    is_available_badge.short_description = "Disponibilidad"
