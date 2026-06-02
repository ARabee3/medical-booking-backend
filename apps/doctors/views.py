"""
Doctors app views.

Endpoints:
- GET /api/doctors/               → list approved doctors
- GET /api/doctors/<id>/          → single doctor profile
- GET /api/doctors/<id>/availability/?date=YYYY-MM-DD → free slots
"""

# Standard library
from datetime import date as dt_date

# Third-party packages
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

# Django
from django.db.models import Q

# Local / project imports
from apps.doctors.models import DoctorProfile, Availability
from shared.pagination import StandardResultsSetPagination
from .serializers import DoctorDetailSerializer, DoctorListSerializer


class DoctorListView(generics.ListAPIView):
    """List all approved and active doctors.

    Query parameters:
        specialty (str) -- case-insensitive exact match on specialty name
        search (str)    -- case-insensitive search on first or last name
    """

    serializer_class = DoctorListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            DoctorProfile.objects
            .filter(user__is_active=True, user__is_approved=True)
            .select_related("user", "specialty")
        )

        # Filter by specialty name
        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialty__name__iexact=specialty)

        # Search by doctor name (first or last)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return qs.order_by("user__first_name", "user__last_name")


class DoctorDetailView(generics.RetrieveAPIView):
    """Retrieve a single approved doctor's profile."""

    serializer_class = DoctorDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            DoctorProfile.objects
            .filter(user__is_active=True, user__is_approved=True)
            .select_related("user", "specialty")
        )

    def handle_exception(self, exc):
        """Override to return a cleaner 404 message."""
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            response.data = {"detail": "Doctor not found"}
        return response


class AvailabilityListView(APIView):
    """List available time slots for a doctor on a given date.

    Query parameters:
        date (str, required) -- YYYY-MM-DD format

    Response shape:
        { "doctor_id": 1, "date": "2026-01-20", "slots": ["09:00", ...] }
    """

    def get(self, request, pk: int):
        # Validate the doctor exists and is active/approved
        try:
            doctor = (
                DoctorProfile.objects
                .filter(user__is_active=True, user__is_approved=True)
                .select_related("user")
                .get(pk=pk)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate date parameter
        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"date": ["This parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            requested_date = dt_date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"date": ["Invalid date format. Use YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only serve slots for today or future dates
        if requested_date < dt_date.today():
            return Response(
                {
                    "doctor_id": doctor.id,
                    "date": date_str,
                    "slots": [],
                }
            )

        # Fetch unbooked slots for this doctor and date
        slots = (
            Availability.objects
            .filter(
                doctor=doctor,
                date=requested_date,
                is_booked=False,
            )
            .values_list("start_time", flat=True)
            .order_by("start_time")
        )

        # Format times as "HH:MM" strings
        slot_times = [s.strftime("%H:%M") for s in slots]

        return Response(
            {
                "doctor_id": doctor.id,
                "date": date_str,
                "slots": slot_times,
            }
        )
