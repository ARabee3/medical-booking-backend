"""
Doctors app URL configuration.

Endpoints:
- GET /api/doctors/
- GET /api/doctors/:id/
- GET /api/doctors/:id/availability/
- GET /api/doctors/:id/availability/summary/
"""

from django.urls import path

from .views import (
    AvailabilityListView,
    AvailabilitySummaryView,
    DoctorDetailView,
    DoctorListView,
)

urlpatterns = [
    path("doctors/", DoctorListView.as_view(), name="doctor-list"),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    path(
        "doctors/<int:pk>/availability/",
        AvailabilityListView.as_view(),
        name="doctor-availability",
    ),
    path(
        "doctors/<int:pk>/availability/summary/",
        AvailabilitySummaryView.as_view(),
        name="doctor-availability-summary",
    ),
]
