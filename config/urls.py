"""
URL configuration for medical-booking-backend.

All API endpoints are prefixed with /api/ to match the frontend contract.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.doctors.urls")),
    path("api/", include("apps.appointments.urls")),
    path("api/", include("apps.admin_api.urls")),
]
