"""
Custom User model for Lexora Library.

Extends Django's AbstractUser with role-based access control,
membership tracking and profile fields.
"""
import uuid
import datetime
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def user_avatar_path(instance: "User", filename: str) -> str:
    """Generate upload path for user avatars."""
    ext = filename.rsplit(".", 1)[-1]
    return f"avatars/{instance.pk}/{uuid.uuid4()}.{ext}"


class UserManager(BaseUserManager):
    """Custom manager with helper querysets and user creation methods."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "member")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)

    def active_members(self):
        return self.filter(role=User.Role.MEMBER, is_active=True)

    def librarians(self):
        return self.filter(role=User.Role.LIBRARIAN, is_active=True)

    def with_active_loans(self):
        return self.filter(loans__status="borrowed").distinct()


class User(AbstractUser):
    """
    Custom user model for Lexora Library.

    Roles:
        - admin: Full system access
        - librarian: Manage books, loans, users
        - member: Standard library member
    """

    class Role(models.TextChoices):
        ADMIN = "admin", _("Administrador")
        LIBRARIAN = "librarian", _("Bibliotecario")
        MEMBER = "member", _("Miembro")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Override email to make it unique and required
    email = models.EmailField(_("email address"), unique=True)

    # Profile
    avatar = models.ImageField(
        _("avatar"),
        upload_to=user_avatar_path,
        null=True,
        blank=True,
    )
    phone = models.CharField(_("teléfono"), max_length=20, blank=True)
    bio = models.TextField(_("biografía"), blank=True, max_length=500)

    # Role & membership
    role = models.CharField(
        _("rol"),
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )
    membership_date = models.DateField(
        _("fecha de membresía"),
        default=datetime.date.today,
    )
    membership_number = models.CharField(
        _("número de membresía"),
        max_length=20,
        unique=True,
        blank=True,
    )

    # Preferences
    dark_mode = models.BooleanField(_("modo oscuro"), default=True)
    email_notifications = models.BooleanField(_("notificaciones por email"), default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()  # type: ignore

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_librarian(self) -> bool:
        return self.role in (self.Role.LIBRARIAN, self.Role.ADMIN) or self.is_superuser

    @property
    def is_member(self) -> bool:
        return self.role == self.Role.MEMBER

    @property
    def full_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def active_loan_count(self) -> int:
        return self.loans.filter(status="borrowed").count()

    def save(self, *args, **kwargs) -> None:
        if not self.membership_number:
            # Auto-generate membership number
            import secrets
            self.membership_number = f"LX-{secrets.token_hex(4).upper()}"
        super().save(*args, **kwargs)
