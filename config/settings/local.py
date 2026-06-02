"""
Local development settings.

By default, inherits PostgreSQL config from base.py (which reads from .env).
To use SQLite for quick testing without PostgreSQL, set USE_SQLITE=true in .env.
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Opt-in SQLite for quick testing (default: PostgreSQL from base.py)
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

# Console email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Add django-extensions for development
INSTALLED_APPS += ["django_extensions"]  # noqa: F405

# Log SQL queries in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
