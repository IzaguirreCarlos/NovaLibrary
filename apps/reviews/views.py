"""Web views for book reviews."""
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from apps.reviews.models import Review
from apps.books.models import Book


class CreateReviewView(LoginRequiredMixin, View):
    """Handle review creation from the book detail page."""

    def post(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id, is_active=True)

        if Review.objects.filter(user=request.user, book=book).exists():
            messages.error(request, "Ya has escrito una reseña para este libro.")
            return redirect("books:detail", slug=book.slug)

        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()
        title = request.POST.get("title", "").strip()

        if not rating or not comment:
            messages.error(request, "La calificación y el comentario son obligatorios.")
            return redirect("books:detail", slug=book.slug)

        try:
            rating_int = int(rating)
            if not (1 <= rating_int <= 5):
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "La calificación debe ser un número entre 1 y 5.")
            return redirect("books:detail", slug=book.slug)

        Review.objects.create(
            user=request.user,
            book=book,
            rating=rating_int,
            title=title,
            comment=comment,
        )
        messages.success(request, "¡Reseña publicada correctamente!")
        return redirect("books:detail", slug=book.slug)


class DeleteReviewView(LoginRequiredMixin, View):
    """Allow a user to delete their own review."""

    def post(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)

        if not (request.user == review.user or request.user.is_librarian):
            messages.error(request, "No tienes permiso para eliminar esta reseña.")
            return redirect("books:detail", slug=review.book.slug)

        book_slug = review.book.slug
        review.delete()
        messages.success(request, "Reseña eliminada.")
        return redirect("books:detail", slug=book_slug)


class EditReviewView(LoginRequiredMixin, View):
    """Allow a user to edit their own review."""

    def post(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id, user=request.user)

        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()
        title = request.POST.get("title", "").strip()

        if not rating or not comment:
            messages.error(request, "La calificación y el comentario son obligatorios.")
            return redirect("books:detail", slug=review.book.slug)

        try:
            rating_int = int(rating)
            if not (1 <= rating_int <= 5):
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "La calificación debe ser un número entre 1 y 5.")
            return redirect("books:detail", slug=review.book.slug)

        review.rating = rating_int
        review.comment = comment
        review.title = title
        review.save(update_fields=["rating", "comment", "title", "updated_at"])
        messages.success(request, "Reseña actualizada correctamente.")
        return redirect("books:detail", slug=review.book.slug)
