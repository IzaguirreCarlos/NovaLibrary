"""Reusable mixins for views and models."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages


class LibrarianRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires Librarian or Admin role."""

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.role in ("librarian", "admin")

    def handle_no_permission(self) -> HttpResponse:
        messages.error(self.request, "Acceso restringido. Se requieren permisos de bibliotecario.")
        return redirect("dashboard:home")


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires Admin role."""

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and (user.role == "admin" or user.is_superuser)

    def handle_no_permission(self) -> HttpResponse:
        messages.error(self.request, "Acceso restringido. Se requieren permisos de administrador.")
        return redirect("dashboard:home")


class HtmxMixin:
    """Mixin for handling HTMX requests with different templates."""

    htmx_template: str | None = None

    def get_template_names(self) -> list[str]:
        if self.request.htmx and self.htmx_template:
            return [self.htmx_template]
        return super().get_template_names()
