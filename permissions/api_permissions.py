"""Custom DRF permissions for Lexora Library API."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Allow access only to Admin users."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsLibrarian(BasePermission):
    """Allow access to Librarian and Admin users."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_librarian)


class IsOwnerOrLibrarian(BasePermission):
    """
    Object-level permission:
    - Librarians/Admins: full access
    - Others: only their own objects
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.is_librarian:
            return True
        # Check if the object belongs to the user
        owner = getattr(obj, "user", None)
        return owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    """Allow read to all authenticated, write only to owner."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None)
        return owner == request.user


class ReadOnlyOrLibrarian(BasePermission):
    """Safe methods for all authenticated, write for librarians."""

    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_librarian
