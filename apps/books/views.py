"""Book views for the web interface."""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from .models import Book, Author, Category
from repositories.book_repository import BookRepository


class BookListView(LoginRequiredMixin, ListView):
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        category = self.request.GET.get("category", "")
        language = self.request.GET.get("language", "")
        return BookRepository.search(query=query, category_slug=category, language=language)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["languages"] = Book.Language.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["selected_language"] = self.request.GET.get("language", "")
        return ctx


class BookDetailView(LoginRequiredMixin, DetailView):
    template_name = "books/book_detail.html"
    context_object_name = "book"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Book.objects.filter(is_active=True).select_related("publisher").prefetch_related(
            "authors", "categories", "reviews__user"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        book = self.object
        ctx["reviews"] = book.reviews.filter(is_approved=True).select_related("user")[:10]
        ctx["related_books"] = (
            Book.objects.filter(categories__in=book.categories.all(), is_active=True)
            .exclude(pk=book.pk)
            .distinct()[:6]
        )
        # Check if user already has this book borrowed
        if self.request.user.is_authenticated:
            ctx["user_has_loan"] = book.loans.filter(
                user=self.request.user, status="borrowed"
            ).exists()
            ctx["user_review"] = book.reviews.filter(user=self.request.user).first()
        return ctx


class AuthorDetailView(LoginRequiredMixin, DetailView):
    model = Author
    template_name = "books/author_detail.html"
    context_object_name = "author"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["books"] = self.object.books.filter(is_active=True).annotate(
            avg_rating=Avg("reviews__rating")
        )
        return ctx
