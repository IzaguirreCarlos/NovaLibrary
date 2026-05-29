"""
Book, Author, Category and Publisher models for Lexora Library.

Enterprise-grade catalog management with full inventory control.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


def book_cover_path(instance: "Book", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1]
    return f"books/covers/{instance.isbn}/{uuid.uuid4()}.{ext}"


def author_photo_path(instance: "Author", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1]
    return f"authors/{instance.pk}/{uuid.uuid4()}.{ext}"


# ─── Author ───────────────────────────────────────────────────────────────────

class Author(models.Model):
    """Author with biography and profile information."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(_("nombre completo"), max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    biography = models.TextField(_("biografía"), blank=True)
    birth_date = models.DateField(_("fecha de nacimiento"), null=True, blank=True)
    death_date = models.DateField(_("fecha de fallecimiento"), null=True, blank=True)
    nationality = models.CharField(_("nacionalidad"), max_length=100, blank=True)
    profile_image = models.ImageField(
        _("foto de perfil"),
        upload_to=author_photo_path,
        null=True,
        blank=True,
    )
    website = models.URLField(_("sitio web"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("autor")
        verbose_name_plural = _("autores")
        ordering = ["full_name"]
        indexes = [models.Index(fields=["full_name"])]

    def __str__(self) -> str:
        return self.full_name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.full_name)
        super().save(*args, **kwargs)

    @property
    def book_count(self) -> int:
        return self.books.count()


# ─── Publisher ────────────────────────────────────────────────────────────────

class Publisher(models.Model):
    """Book publisher."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nombre"), max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    country = models.CharField(_("país"), max_length=100, blank=True)
    website = models.URLField(_("sitio web"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("editorial")
        verbose_name_plural = _("editoriales")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─── Category ─────────────────────────────────────────────────────────────────

class Category(models.Model):
    """Book category / genre."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nombre"), max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(_("descripción"), blank=True)
    icon = models.CharField(_("ícono"), max_length=50, blank=True, help_text="Lucide icon name")
    color = models.CharField(_("color"), max_length=7, default="#6366f1", help_text="Hex color")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("categoría")
        verbose_name_plural = _("categorías")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ─── Book Manager ─────────────────────────────────────────────────────────────

class BookManager(models.Manager):
    """Custom manager for books with optimized querysets."""

    def available(self):
        """Books with available stock."""
        return self.filter(available_stock__gt=0, is_active=True)

    def featured(self):
        """Featured books."""
        return self.filter(is_featured=True, is_active=True)

    def with_details(self):
        """Books with related objects pre-fetched."""
        return self.select_related("publisher").prefetch_related("authors", "categories")

    def popular(self):
        """Books ordered by loan count."""
        return self.annotate(
            loan_count=models.Count("loans")
        ).order_by("-loan_count")

    def top_rated(self):
        """Books ordered by average rating."""
        return self.annotate(
            avg_rating=models.Avg("reviews__rating")
        ).order_by("-avg_rating")


# ─── Book ─────────────────────────────────────────────────────────────────────

class Book(models.Model):
    """
    Main book model with full bibliographic information.

    Tracks both total stock and available stock to manage loans.
    """

    class Language(models.TextChoices):
        SPANISH = "es", _("Español")
        ENGLISH = "en", _("Inglés")
        FRENCH = "fr", _("Francés")
        GERMAN = "de", _("Alemán")
        PORTUGUESE = "pt", _("Portugués")
        ITALIAN = "it", _("Italiano")
        OTHER = "other", _("Otro")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Bibliographic info
    title = models.CharField(_("título"), max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True)
    subtitle = models.CharField(_("subtítulo"), max_length=300, blank=True)
    isbn = models.CharField(_("ISBN"), max_length=17, unique=True, db_index=True)
    description = models.TextField(_("descripción"), blank=True)
    publication_date = models.DateField(_("fecha de publicación"), null=True, blank=True)
    language = models.CharField(
        _("idioma"),
        max_length=10,
        choices=Language.choices,
        default=Language.SPANISH,
    )
    pages = models.PositiveIntegerField(
        _("páginas"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    edition = models.CharField(_("edición"), max_length=50, blank=True)

    # Relations
    authors = models.ManyToManyField(Author, related_name="books", verbose_name=_("autores"))
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
        verbose_name=_("editorial"),
    )
    categories = models.ManyToManyField(Category, related_name="books", verbose_name=_("categorías"))

    # Cover image
    cover_image = models.ImageField(
        _("portada"),
        upload_to=book_cover_path,
        null=True,
        blank=True,
    )

    # Inventory
    stock = models.PositiveIntegerField(_("stock total"), default=1)
    available_stock = models.PositiveIntegerField(_("stock disponible"), default=1)

    # Metadata
    is_active = models.BooleanField(_("activo"), default=True, db_index=True)
    is_featured = models.BooleanField(_("destacado"), default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BookManager()

    class Meta:
        verbose_name = _("libro")
        verbose_name_plural = _("libros")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["isbn"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["available_stock"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} (ISBN: {self.isbn})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.isbn}")
        super().save(*args, **kwargs)

    @property
    def is_available(self) -> bool:
        return self.available_stock > 0 and self.is_active

    @property
    def availability_percentage(self) -> float:
        if self.stock == 0:
            return 0
        return round((self.available_stock / self.stock) * 100, 1)

    @property
    def average_rating(self) -> float:
        result = self.reviews.aggregate(avg=models.Avg("rating"))
        return round(result["avg"] or 0, 1)

    @property
    def review_count(self) -> int:
        return self.reviews.count()

    @property
    def author_names(self) -> str:
        return ", ".join(a.full_name for a in self.authors.all())
