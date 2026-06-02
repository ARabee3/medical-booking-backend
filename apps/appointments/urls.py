from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.appointments.views import (
    AvailabilityViewSet,
    DoctorAppointmentDetailView,
    DoctorAppointmentListView,
    PatientAppointmentDetailView,
    PatientAppointmentListCreateView,
)

router = DefaultRouter()
router.register(
    prefix="doctor/availability",
    viewset=AvailabilityViewSet,
    basename="availability",
)

urlpatterns = [
    path("appointments/", PatientAppointmentListCreateView.as_view(), name="appointment-list"),
    path("appointments/<int:pk>/", PatientAppointmentDetailView.as_view(), name="appointment-detail"),
    path("doctor/appointments/", DoctorAppointmentListView.as_view(), name="doctor-appointment-list"),
    path("doctor/appointments/<int:pk>/", DoctorAppointmentDetailView.as_view(), name="doctor-appointment-detail"),
]

urlpatterns += router.urls
