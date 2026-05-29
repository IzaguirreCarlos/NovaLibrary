"""Books app configuration."""
from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.books"
    verbose_name = "Catálogo de Libros"

    def ready(self) -> None:
        import apps.books.signals  # noqa: F401
