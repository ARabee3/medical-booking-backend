"""
Appointments app URL configuration.

Endpoints:
- GET/POST  /api/appointments/            BE-011 (PatientAppointmentListCreateView)
- PATCH     /api/appointments/:id/        BE-012 (PatientAppointmentDetailView)
- GET       /api/doctor/appointments/     BE-013 (DoctorAppointmentListView)
- PATCH     /api/doctor/appointments/:id/ BE-014 (DoctorAppointmentDetailView)
- POST      /api/doctor/availability/     BE-015 (AvailabilityManagementView)
- DELETE    /api/doctor/availability/:id/ BE-015 (AvailabilityManagementView)
"""

from django.urls import path

from apps.appointments.views import (
    PatientAppointmentListCreateView,
    PatientAppointmentDetailView,
    DoctorAppointmentListView,
    DoctorAppointmentDetailView,
)

urlpatterns = [
    # BE-011: Patient list + book
    path("appointments/", PatientAppointmentListCreateView.as_view(), name="appointment-list"),
    # BE-012: Patient cancel/reschedule
    path("appointments/<int:pk>/", PatientAppointmentDetailView.as_view(), name="appointment-detail"),
    # BE-013: Doctor appointment list
    path("doctor/appointments/", DoctorAppointmentListView.as_view(), name="doctor-appointment-list"),
    # BE-014: Doctor cancel/confirm
    path("doctor/appointments/<int:pk>/", DoctorAppointmentDetailView.as_view(), name="doctor-appointment-detail"),
    # BE-015: path("doctor/availability/", AvailabilityManagementView.as_view(), name="doctor-availability-list"),
    # BE-015: path("doctor/availability/<int:pk>/", AvailabilityManagementView.as_view(), name="doctor-availability-detail"),
]

