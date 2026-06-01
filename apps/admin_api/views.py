# Third-party packages
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

# Django
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

# Local / project imports
from shared.permissions import IsAdmin
from apps.appointments.models import Appointment
from apps.admin_api.filters import AppointmentFilter, UserFilter
from apps.admin_api.serializers import (
    AdminAppointmentSerializer,
    AdminStatsSerializer,
    AdminUserSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# BE-016 — User management views
# ---------------------------------------------------------------------------

class AdminUserListView(generics.ListAPIView):
    """List all users in the system with optional filtering and search.

    GET /api/admin/users/
    Accessible only by users with the ADMIN role.
    Supports filter params: role, is_active, is_approved, search.
    """

    serializer_class   = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends    = [DjangoFilterBackend]
    filterset_class    = UserFilter

    def get_queryset(self):
        return User.objects.all().order_by("id")


class AdminUserUpdateView(generics.UpdateAPIView):
    """Update a user's is_active or is_approved status.

    PATCH /api/admin/users/<id>/
    Accessible only by users with the ADMIN role.
    Only is_active and is_approved are writable (enforced by serializer).
    """

    serializer_class   = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    http_method_names  = ["patch"]  # Disable PUT — PATCH only per API contract

    def get_queryset(self):
        return User.objects.all()


# ---------------------------------------------------------------------------
# BE-017 — Appointment overview view
# ---------------------------------------------------------------------------

class AdminAppointmentListView(generics.ListAPIView):
    """List all appointments across the system with filtering and ordering.

    GET /api/admin/appointments/
    Accessible only by users with the ADMIN role.

    Filter params : status, date_from, date_to
    Ordering params: date, status (prefix with '-' for descending)
        e.g. ?ordering=-date&status=PENDING&date_from=2026-01-01
    """

    serializer_class   = AdminAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = AppointmentFilter
    ordering_fields    = ["date", "status"]
    ordering           = ["-date"]  # Default: newest first

    def get_queryset(self):
        # select_related pulls doctor, patient, and doctor's profile + specialty
        # in 1 query instead of N+1 on serializer access
        return (
            Appointment.objects
            .select_related(
                "doctor",
                "doctor__doctor_profile",
                "doctor__doctor_profile__specialty",
                "patient",
            )
            .all()
        )


# ---------------------------------------------------------------------------
# BE-018 — Dashboard stats view
# ---------------------------------------------------------------------------

class AdminStatsView(APIView):
    """Return a flat snapshot of system-wide counts for the admin dashboard.

    GET /api/admin/stats/
    Accessible only by users with the ADMIN role.

    Response:
        total_users        -- all registered users
        total_doctors      -- users with role=DOCTOR
        total_appointments -- all appointment records
        pending_approvals  -- doctors awaiting admin approval
                             (role=DOCTOR, is_approved=False)
    """

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        # Single aggregated query instead of 4 separate .count() calls
        user_counts = User.objects.aggregate(
            total_users=Count("id"),
            total_doctors=Count("id", filter=Q(role="DOCTOR")),
            pending_approvals=Count(
                "id", filter=Q(role="DOCTOR", is_approved=False)
            ),
        )

        stats = {
            **user_counts,
            "total_appointments": Appointment.objects.count(),
        }

        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data)