"""
Celery tasks for Lexora Library notifications and scheduled operations.

Scheduled tasks:
  - process_overdue_loans: daily at 00:05
  - send_due_reminders_3_days: daily at 09:00
  - send_due_reminders_1_day: daily at 09:00
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger("lexora.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_overdue_loans_task(self):
    """
    Mark overdue loans and send notifications.
    Runs daily at midnight.
    """
    try:
        from services.loan_service import LoanService
        service = LoanService()
        count = service.process_overdue_loans()
        logger.info("Overdue task completed: %d loans processed", count)
        return {"processed": count}
    except Exception as exc:
        logger.error("Overdue task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_due_reminder_task(self, days_before: int = 3):
    """
    Send email reminders for loans due in `days_before` days.
    """
    try:
        from services.loan_service import LoanService
        service = LoanService()
        count = service.send_due_reminders(days_before=days_before)
        logger.info("Reminder task (%dd) completed: %d emails queued", days_before, count)
        return {"reminders_sent": count, "days_before": days_before}
    except Exception as exc:
        logger.error("Reminder task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_loan_confirmation_email(self, loan_id: str):
    """Send email confirmation when a loan is created."""
    try:
        from apps.loans.models import Loan
        loan = Loan.objects.select_related("user", "book").get(pk=loan_id)
        subject = f"Préstamo aprobado: {loan.book.title}"
        message = (
            f"Hola {loan.user.first_name},\n\n"
            f"Tu préstamo de \"{loan.book.title}\" ha sido aprobado.\n"
            f"Fecha de devolución: {loan.due_date.strftime('%d/%m/%Y')}\n\n"
            f"Lexora Library"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[loan.user.email],
            fail_silently=True,
        )
        logger.info("Loan confirmation email sent: %s → %s", loan_id, loan.user.email)
    except Exception as exc:
        logger.error("Email task failed for loan %s: %s", loan_id, exc)
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_notifications():
    """Remove read notifications older than 30 days."""
    from datetime import timedelta
    from django.utils import timezone
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    count, _ = Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()
    logger.info("Cleaned up %d old notifications", count)
    return count
