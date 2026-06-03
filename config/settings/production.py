"""
Production settings.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# SECURITY: Use a strong secret key from environment
SECRET_KEY = os.getenv("SECRET_KEY")  # noqa: F405
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# Update allowed hosts from environment
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")  # noqa: F405
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise ValueError("ALLOWED_HOSTS environment variable is required in production")

# Security headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files via whitenoise
INSTALLED_APPS += ["whitenoise.runserver_nostatic"]  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# CORS: configure from environment
cors_allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in cors_allowed_origins_env.split(",") if origin.strip()
]


# Database: use DATABASE_URL if provided
database_url = os.getenv("DATABASE_URL")  # noqa: F405
if database_url:
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(database_url)  # noqa: F405
