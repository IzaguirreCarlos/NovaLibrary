# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System dependencies for Pillow, psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements/ requirements/
RUN pip install --prefix=/install -r requirements/production.txt


# ── Stage 2: Development ─────────────────────────────────────────────────────
FROM builder AS development

COPY requirements/development.txt requirements/development.txt
RUN pip install --prefix=/install -r requirements/development.txt

ENV PYTHONPATH=/install/lib/python3.12/site-packages \
    PATH=/install/bin:$PATH

WORKDIR /app

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r lexora && useradd -r -g lexora lexora

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs media staticfiles \
    && chown -R lexora:lexora /app

USER lexora

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings.production || true

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/', timeout=5)" || exit 1

# Run gunicorn
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
