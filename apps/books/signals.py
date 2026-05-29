"""Signals for the books app."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Book


@receiver(post_save, sender=Book)
def invalidate_book_cache(sender, instance: Book, **kwargs) -> None:
    """Clear book-related caches when a book is saved."""
    cache.delete_many([
        f"book_detail_{instance.pk}",
        f"book_detail_{instance.slug}",
        "book_list_featured",
        "book_list_popular",
        "book_list_top_rated",
        "dashboard_stats",
    ])


@receiver(post_delete, sender=Book)
def invalidate_book_cache_on_delete(sender, instance: Book, **kwargs) -> None:
    """Clear caches when a book is deleted."""
    cache.delete_many([
        f"book_detail_{instance.pk}",
        f"book_detail_{instance.slug}",
        "book_list_featured",
        "dashboard_stats",
    ])
