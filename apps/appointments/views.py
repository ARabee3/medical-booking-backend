"""
Appointments app views.

PatientAppointmentListCreateView: GET + POST /api/appointments/
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from shared.pagination import StandardResultsSetPagination
from shared.permissions import IsPatient, IsDoctor

from apps.appointments.models import Appointment
from apps.appointments.serializers import (
    AppointmentReadSerializer,
    AppointmentWriteSerializer,
    AppointmentUpdateSerializer,
    DoctorAppointmentReadSerializer,
)


class PatientAppointmentListCreateView(generics.ListCreateAPIView):
    """List and book appointments for the authenticated patient.

    GET:  Returns all appointments belonging to request.user (patient).
    POST: Validates and books a new appointment via the booking service.
    """

    permission_classes = [permissions.IsAuthenticated, IsPatient]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Use the write serializer for POST; read serializer for GET."""
        if self.request.method == "POST":
            return AppointmentWriteSerializer
        return AppointmentReadSerializer

    def get_queryset(self):
        """Return only appointments owned by the current patient.

        select_related prevents N+1 queries when rendering nested doctor info.
        """
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related(
                "doctor",
                "doctor__doctor_profile",
                "doctor__doctor_profile__specialty",
            )
        )

    def create(self, request, *args, **kwargs):
        """Validate input, book the appointment, return the read-shape response."""
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        appointment = write_serializer.save()

        # Re-serialize with read serializer to match the API contract output shape
        read_serializer = AppointmentReadSerializer(
            appointment,
            context={"request": request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class PatientAppointmentDetailView(generics.UpdateAPIView):
    """Modify an existing appointment for the authenticated patient.

    PATCH: Cancels or reschedules the appointment based on input.
    Only the owning patient can modify the appointment.
    """

    permission_classes = [permissions.IsAuthenticated, IsPatient]
    serializer_class = AppointmentUpdateSerializer

    def get_queryset(self):
        """Return only appointments owned by the current patient."""
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related(
                "doctor",
                "doctor__doctor_profile",
                "doctor__doctor_profile__specialty",
            )
        )

    def update(self, request, *args, **kwargs):
        """Validate input and apply the appropriate modification via services."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        from apps.appointments.services import cancel_appointment, reschedule_appointment

        validated_data = serializer.validated_data

        if validated_data.get("status") == "CANCELLED":
            appointment = cancel_appointment(appointment=instance)
        else:
            appointment = reschedule_appointment(
                appointment=instance,
                new_date=validated_data["date"],
                new_time=validated_data["time"],
            )

        # Return the updated appointment using the read serializer
        read_serializer = AppointmentReadSerializer(
            appointment,
            context={"request": request},
        )
        return Response(read_serializer.data)


class DoctorAppointmentListView(generics.ListAPIView):
    """List appointments for the authenticated doctor.

    GET: Returns all appointments where doctor=request.user.
    Includes nested patient information.
    """

    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = DoctorAppointmentReadSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Return only appointments owned by the current doctor."""
        return (
            Appointment.objects.filter(doctor=self.request.user)
            .select_related("patient")
            .order_by("-date", "-time")
        )
