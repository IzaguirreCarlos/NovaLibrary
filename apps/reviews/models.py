"""
Review and Rating model for Lexora Library.

Each user can review a book once. Ratings are 1–5 stars.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ReviewManager(models.Manager):
    """Custom queryset for reviews."""

    def approved(self):
        return self.filter(is_approved=True)

    def pending(self):
        return self.filter(is_approved=False)

    def by_book(self, book):
        return self.filter(book=book, is_approved=True).select_related("user").order_by("-created_at")


class Review(models.Model):
    """User review and star rating for a book."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("usuario"),
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("libro"),
    )

    rating = models.PositiveSmallIntegerField(
        _("calificación"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(_("título"), max_length=200, blank=True)
    comment = models.TextField(_("comentario"), max_length=2000)

    is_approved = models.BooleanField(_("aprobada"), default=True, db_index=True)
    helpful_count = models.PositiveIntegerField(_("votos útiles"), default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReviewManager()

    class Meta:
        verbose_name = _("reseña")
        verbose_name_plural = _("reseñas")
        ordering = ["-created_at"]
        unique_together = [("user", "book")]
        indexes = [
            models.Index(fields=["book", "is_approved"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.book.title} ({self.rating}★)"

    @property
    def star_display(self) -> str:
        return "★" * self.rating + "☆" * (5 - self.rating)
