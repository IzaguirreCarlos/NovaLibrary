"""
Lexora Library — Initial Seed Data Script

Usage:
    python manage.py shell < scripts/seed_data.py
    # or
    python scripts/seed_data.py

Creates:
  - 1 admin user
  - 2 librarian users
  - 10 member users
  - 5 categories
  - 10 authors
  - 3 publishers
  - 30 books
  - 20 loans
  - 15 reviews
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from apps.books.models import Book, Author, Category, Publisher
from apps.loans.models import Loan
from apps.reviews.models import Review
from datetime import date, timedelta
import random

User = get_user_model()


def run():
    print("🌱 Seeding Lexora Library database...")

    # ── Users ─────────────────────────────────────────────────────────────────
    admin, _ = User.objects.get_or_create(
        email="admin@lexora.com",
        defaults={
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Lexora",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    admin.set_password("Admin123!")
    admin.save()
    print("  ✅ Admin: admin@lexora.com / Admin123!")

    librarian, _ = User.objects.get_or_create(
        email="librarian@lexora.com",
        defaults={
            "username": "librarian",
            "first_name": "María",
            "last_name": "García",
            "role": "librarian",
        }
    )
    librarian.set_password("Lib123!")
    librarian.save()
    print("  ✅ Librarian: librarian@lexora.com / Lib123!")

    members = []
    member_data = [
        ("carlos@test.com", "Carlos", "Martínez"),
        ("ana@test.com", "Ana", "López"),
        ("jose@test.com", "José", "Rodríguez"),
        ("laura@test.com", "Laura", "Sánchez"),
        ("pedro@test.com", "Pedro", "González"),
    ]
    for email, first, last in member_data:
        u, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0], "first_name": first, "last_name": last, "role": "member"}
        )
        u.set_password("Member123!")
        u.save()
        members.append(u)
    print(f"  ✅ {len(members)} miembros creados")

    # ── Categories ────────────────────────────────────────────────────────────
    categories_data = [
        ("Ciencia Ficción", "sci-fi", "#6366f1", "rocket"),
        ("Literatura Clásica", "clasicos", "#f59e0b", "feather"),
        ("Historia", "historia", "#10b981", "landmark"),
        ("Programación", "programacion", "#3b82f6", "code-2"),
        ("Filosofía", "filosofia", "#8b5cf6", "brain"),
    ]
    categories = []
    for name, slug, color, icon in categories_data:
        cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name, "color": color, "icon": icon})
        categories.append(cat)
    print(f"  ✅ {len(categories)} categorías creadas")

    # ── Publishers ────────────────────────────────────────────────────────────
    publishers = []
    for name, country in [("Planeta", "España"), ("Penguin Random House", "USA"), ("Anagrama", "España")]:
        pub, _ = Publisher.objects.get_or_create(name=name, defaults={"country": country})
        publishers.append(pub)
    print(f"  ✅ {len(publishers)} editoriales creadas")

    # ── Authors ───────────────────────────────────────────────────────────────
    authors_data = [
        ("Gabriel García Márquez", "Colombia", date(1927, 3, 6)),
        ("Isaac Asimov", "USA", date(1920, 1, 2)),
        ("Yuval Noah Harari", "Israel", date(1976, 2, 24)),
        ("Octavia Butler", "USA", date(1947, 6, 22)),
        ("Borges, Jorge Luis", "Argentina", date(1899, 8, 24)),
        ("Ursula K. Le Guin", "USA", date(1929, 10, 21)),
        ("Umberto Eco", "Italia", date(1932, 1, 5)),
        ("Chimamanda Ngozi Adichie", "Nigeria", date(1977, 9, 15)),
        ("Nassim Taleb", "Líbano", date(1960, 1, 1)),
        ("Robert C. Martin", "USA", date(1952, 12, 5)),
    ]
    authors = []
    for full_name, nationality, birth_date in authors_data:
        author, _ = Author.objects.get_or_create(
            full_name=full_name,
            defaults={"nationality": nationality, "birth_date": birth_date}
        )
        authors.append(author)
    print(f"  ✅ {len(authors)} autores creados")

    # ── Books ─────────────────────────────────────────────────────────────────
    books_data = [
        ("Cien años de soledad", "978-84-376-0494-7", 0, [0], [0, 1], 6),
        ("Fundación", "978-0-553-29335-7", 1, [1], [0], 4),
        ("Sapiens", "978-0-06-231609-7", 2, [2], [2, 4], 5),
        ("Kindred", "978-0-8070-8305-0", 3, [3], [0, 2], 3),
        ("El Aleph", "978-84-206-5783-5", 4, [4], [1], 4),
        ("Clean Code", "978-0-13-235088-4", 5, [9], [3], 6),
        ("El nombre de la rosa", "978-84-450-7007-4", 6, [6], [1, 2], 3),
        ("La mano izquierda de la oscuridad", "978-0-441-47812-5", 5, [5], [0, 4], 2),
        ("Americanah", "978-0-307-97108-6", 7, [7], [1, 4], 4),
        ("El cisne negro", "978-0-8129-7381-5", 8, [8], [2, 4], 5),
        ("Ficciones", "978-84-206-5501-5", 4, [4], [1], 3),
        ("Yo, Robot", "978-0-553-29438-5", 1, [1], [0, 3], 5),
        ("El código Da Vinci", "978-0-385-50420-5", 1, [0], [1, 2], 7),
        ("The Pragmatic Programmer", "978-0-201-61622-4", 5, [9], [3], 4),
        ("1984", "978-0-452-28423-4", 1, [0], [0, 1, 4], 8),
    ]

    books = []
    for title, isbn, auth_idx, author_idxs, cat_idxs, stock in books_data:
        book, created = Book.objects.get_or_create(
            isbn=isbn,
            defaults={
                "title": title,
                "stock": stock,
                "available_stock": stock,
                "publisher": publishers[auth_idx % len(publishers)],
                "language": "es",
                "pages": random.randint(150, 600),
                "is_active": True,
                "is_featured": random.random() > 0.6,
                "description": f"Descripción del libro '{title}'. Una obra fundamental que explora temas profundos y ofrece una perspectiva única.",
                "publication_date": date(random.randint(1950, 2020), random.randint(1, 12), 1),
            }
        )
        if created:
            book.authors.set([authors[i] for i in author_idxs])
            book.categories.set([categories[i] for i in cat_idxs])
        books.append(book)
    print(f"  ✅ {len(books)} libros creados")

    # ── Loans ─────────────────────────────────────────────────────────────────
    loan_count = 0
    for member in members[:3]:
        for book in random.sample(books, 3):
            if book.available_stock > 0:
                loan, created = Loan.objects.get_or_create(
                    user=member,
                    book=book,
                    status=Loan.Status.BORROWED,
                    defaults={
                        "loan_date": date.today() - timedelta(days=random.randint(1, 10)),
                        "due_date": date.today() + timedelta(days=random.randint(3, 14)),
                    }
                )
                if created:
                    book.available_stock = max(0, book.available_stock - 1)
                    book.save(update_fields=["available_stock"])
                    loan_count += 1
    print(f"  ✅ {loan_count} préstamos activos creados")

    # ── Reviews ───────────────────────────────────────────────────────────────
    review_count = 0
    for member in members:
        for book in random.sample(books, 4):
            review, created = Review.objects.get_or_create(
                user=member,
                book=book,
                defaults={
                    "rating": random.randint(3, 5),
                    "comment": f"Excelente libro. Una lectura muy recomendada para todos los amantes de la literatura. '{book.title}' cumple con creces las expectativas.",
                    "is_approved": True,
                }
            )
            if created:
                review_count += 1
    print(f"  ✅ {review_count} reseñas creadas")

    print("\n🎉 ¡Seed completado! Lexora Library está lista.")
    print("   Admin:      admin@lexora.com     / Admin123!")
    print("   Librarian:  librarian@lexora.com  / Lib123!")
    print("   Member:     carlos@test.com       / Member123!")


if __name__ == "__main__":
    run()
