"""Development settings for Lexora Library."""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Email: console backend in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Simplified password validation in dev
AUTH_PASSWORD_VALIDATORS = []

# Extra verbose logging in dev
LOGGING["loggers"]["lexora"]["level"] = "DEBUG"  # noqa: F405

# CORS: allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# DRF: show browsable API in dev
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Celery: run tasks eagerly in dev (optional)
CELERY_TASK_ALWAYS_EAGER = False
