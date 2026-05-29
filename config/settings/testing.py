"""Testing settings for Lexora Library."""
from .base import *  # noqa: F401, F403

DEBUG = False

# Use fast password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory SQLite for tests (override in tox for PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable cache in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Email: dummy backend in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery: run tasks eagerly in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable migrations in tests for speed
class DisableMigrations:
    def __contains__(self, item: str) -> bool:
        return True

    def __getitem__(self, item: str) -> None:
        return None

MIGRATION_MODULES = DisableMigrations()  # type: ignore

# No throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# Media files in temp dir
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

# Disable file-based logging in tests
LOGGING["handlers"].pop("file", None)  # noqa: F405
for logger_cfg in LOGGING["loggers"].values():  # noqa: F405
    if "file" in logger_cfg.get("handlers", []):
        logger_cfg["handlers"] = [h for h in logger_cfg["handlers"] if h != "file"]
