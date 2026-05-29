# 📚 Lexora Library

**Sistema de Gestión Bibliotecaria Empresarial** — Una plataforma SaaS moderna construida con Django 5, PostgreSQL, Redis y Celery.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Características

- **Catálogo completo** — Libros, autores, editoriales y categorías con búsqueda avanzada
- **Sistema de préstamos** — Solicitud, devolución, renovación y cálculo automático de multas
- **Dashboard adaptativo** — Vistas distintas para miembros vs bibliotecarios/admin
- **API REST profesional** — DRF + JWT + Swagger/OpenAPI completo
- **Notificaciones** — In-app y email (vencimientos, recordatorios)
- **Seguridad enterprise** — CSRF, XSS, rate limiting, permisos por roles, JWT blacklist
- **Cache inteligente** — Redis con invalidación selectiva
- **Modo oscuro** — UI premium con Tailwind CSS + Alpine.js

---

## 🏗️ Arquitectura

```
lexora/
├── apps/
│   ├── accounts/         # Custom User (admin, librarian, member)
│   ├── books/            # Catálogo: Book, Author, Publisher, Category
│   ├── loans/            # Sistema de préstamos y multas
│   ├── reviews/          # Reseñas y valoraciones
│   ├── notifications/    # Notificaciones in-app + Celery tasks
│   ├── dashboard/        # Vistas adaptativas por rol
│   └── api/              # DRF ViewSets + serializers
├── config/
│   └── settings/         # base, development, production, testing
├── core/                 # Pagination, exceptions, middleware, mixins
├── services/             # Lógica de negocio (LoanService)
├── repositories/         # Data access layer (BookRepository, LoanRepository)
├── permissions/          # Custom DRF permissions
├── templates/            # HTML con Tailwind CSS + HTMX
└── tests/                # Unit + integration + API tests
```

**Patrones utilizados:**
- Service Layer (toda la lógica en `services/`)
- Repository Pattern (queries en `repositories/`)
- Custom Managers en modelos
- Signals para efectos secundarios
- Soft Delete para libros

---

## 🚀 Inicio rápido

### Con Docker (recomendado)

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/lexora-library.git
cd lexora-library

# 2. Configura el entorno
cp .env.example .env

# 3. Levanta todos los servicios
docker compose up -d

# 4. Ejecuta migraciones y seed
docker compose exec web python manage.py migrate
docker compose exec web python scripts/seed_data.py

# 5. Accede a la aplicación
open http://localhost:8000
```

### Sin Docker (desarrollo local)

```bash
# 1. Crea y activa entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instala dependencias
pip install -r requirements/development.txt

# 3. Configura .env
cp .env.example .env
# Edita .env con tus credenciales de PostgreSQL y Redis

# 4. Migraciones y seed
python manage.py migrate
python manage.py createsuperuser
python scripts/seed_data.py

# 5. Celery worker (terminal separada)
celery -A config.celery worker -l info

# 6. Servidor de desarrollo
python manage.py runserver
```

---

## 👤 Cuentas de prueba (seed data)

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Admin | admin@lexora.com | Admin123! |
| Bibliotecario | librarian@lexora.com | Lib123! |
| Miembro | carlos@test.com | Member123! |

---

## 📡 API REST

La API REST está completamente documentada con OpenAPI/Swagger:

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

### Endpoints principales

```
POST   /api/v1/auth/register/        # Registro de usuario
POST   /api/v1/auth/login/           # Login (JWT)
POST   /api/v1/auth/refresh/         # Renovar token
GET    /api/v1/auth/me/              # Perfil actual

GET    /api/v1/books/                # Lista de libros (filtros, búsqueda, paginación)
GET    /api/v1/books/{id}/           # Detalle del libro
POST   /api/v1/books/                # Crear libro (librarian+)
GET    /api/v1/books/featured/       # Libros destacados
GET    /api/v1/books/popular/        # Más prestados
GET    /api/v1/books/top-rated/      # Mejor valorados

GET    /api/v1/authors/              # Lista de autores
GET    /api/v1/categories/           # Categorías

GET    /api/v1/loans/                # Mis préstamos
POST   /api/v1/loans/                # Solicitar préstamo
POST   /api/v1/loans/{id}/return_book/ # Devolver
POST   /api/v1/loans/{id}/renew/    # Renovar
GET    /api/v1/loans/overdue/        # Vencidos (librarian+)
GET    /api/v1/loans/history/        # Historial completo

GET    /api/v1/reviews/?book={id}    # Reseñas de un libro
POST   /api/v1/reviews/              # Crear reseña

GET    /api/v1/dashboard/stats/      # Estadísticas (librarian+)
```

### Autenticación JWT

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lexora.com","password":"Admin123!"}'

# Usar token
curl http://localhost:8000/api/v1/books/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚙️ Variables de entorno

Consulta `.env.example` para la lista completa. Las más importantes:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | *(required)* |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://lexora:lexora@localhost:5432/lexora_db` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `MAX_LOANS_PER_USER` | Máximo préstamos activos | `5` |
| `LOAN_DURATION_DAYS` | Días de préstamo por defecto | `14` |
| `FINE_PER_DAY` | Multa diaria por retraso (USD) | `0.50` |
| `RENEWAL_LIMIT` | Máximo de renovaciones | `2` |

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Solo tests de la API
pytest -m api

# Solo tests unitarios
pytest -m unit
```

Cobertura mínima requerida: **80%**

---

## 🔧 Servicios de infraestructura

| Servicio | Puerto | Descripción |
|---------|--------|-------------|
| Django | 8000 | Aplicación web |
| PostgreSQL | 5432 | Base de datos principal |
| Redis | 6379 | Cache + message broker |
| Celery Worker | — | Procesamiento de tareas |
| Celery Beat | — | Scheduler de tareas periódicas |
| Flower | 5555 | Monitoreo de Celery |

---

## 🛠️ Tareas Celery programadas

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `process_overdue_loans_task` | Diario 00:05 | Marca préstamos vencidos |
| `send_due_reminder_task(3)` | Diario 09:00 | Recordatorio 3 días antes |
| `send_due_reminder_task(1)` | Diario 09:00 | Recordatorio 1 día antes |
| `cleanup_old_notifications` | Semanal | Limpia notificaciones antiguas |

---

## 🏗️ Deployment

### Render / Railway

1. Conecta tu repositorio GitHub
2. Configura las variables de entorno del `.env.example`
3. Cambia `DJANGO_SETTINGS_MODULE=config.settings.production`
4. El CI/CD de GitHub Actions se encarga del despliegue automático

### Variables requeridas en producción

```
SECRET_KEY=<generada-aleatoriamente>
DEBUG=False
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ALLOWED_HOSTS=tudominio.com
SENTRY_DSN=<opcional-para-monitoreo>
```

---

## 📄 Licencia

MIT © 2024 Lexora Library
