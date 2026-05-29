"""Signals for the loans app."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Loan


@receiver(post_save, sender=Loan)
def update_book_stock(sender, instance: Loan, created: bool, **kwargs) -> None:
    """
    Synchronize book available_stock whenever a loan changes status.

    - On create (borrowed): decrement available_stock
    - On return/cancel: increment available_stock
    """
    book = instance.book
    if created and instance.status == Loan.Status.BORROWED:
        # Decrement safely
        from django.db.models import F
        type(book).objects.filter(pk=book.pk).update(
            available_stock=F("available_stock") - 1
        )
    elif not created:
        # Check if transitioning to returned/cancelled
        # We handle this in the service layer to avoid double-counting
        pass

    # Invalidate caches
    cache.delete_many([
        f"book_detail_{book.pk}",
        f"book_detail_{book.slug}",
        "dashboard_stats",
    ])


@receiver(post_save, sender=Loan)
def create_loan_notification(sender, instance: Loan, created: bool, **kwargs) -> None:
    """Create in-app notification for loan events."""
    from apps.notifications.models import Notification

    if created and instance.status == Loan.Status.BORROWED:
        Notification.objects.create(
            user=instance.user,
            type=Notification.Type.LOAN_APPROVED,
            title="Préstamo aprobado",
            message=f'Tu préstamo de "{instance.book.title}" ha sido aprobado. '
                    f'Fecha de devolución: {instance.due_date.strftime("%d/%m/%Y")}.',
            loan_id=instance.pk,
            book_id=instance.book.pk,
        )
