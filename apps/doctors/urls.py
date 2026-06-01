"""
Doctors app URL configuration.

Endpoints:
- GET /api/doctors/
- GET /api/doctors/:id/
- GET /api/doctors/:id/availability/
"""

from django.urls import path

# TODO: Import views once implemented
# from .views import DoctorListView, DoctorDetailView, AvailabilityListView

urlpatterns = [
    # path("doctors/", DoctorListView.as_view(), name="doctor-list"),
    # path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    # path("doctors/<int:pk>/availability/", AvailabilityListView.as_view(), name="doctor-availability"),
]
