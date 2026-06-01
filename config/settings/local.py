"""
Local development settings.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

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
