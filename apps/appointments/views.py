"""
Appointments app views.

PatientAppointmentListCreateView: GET + POST /api/appointments/
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from shared.pagination import StandardResultsSetPagination
from shared.permissions import IsPatient

from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentReadSerializer, AppointmentWriteSerializer


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
