"""
Admin API app configuration.

Provides endpoints for admin dashboard without conflicting
with django.contrib.admin.
"""

from django.apps import AppConfig


class AdminApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_api"
    label = "admin_api"
