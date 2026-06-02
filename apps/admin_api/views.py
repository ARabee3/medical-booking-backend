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
from apps.doctors.models import Specialty
from apps.admin_api.filters import AppointmentFilter, UserFilter
from apps.admin_api.serializers import (
    AdminAppointmentSerializer,
    AdminStatsSerializer,
    AdminUserSerializer,
    SpecialtySerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# BE-016 — User management views
# ---------------------------------------------------------------------------

class AdminUserListView(generics.ListAPIView):
    """List all users. GET /api/admin/users/"""

    serializer_class   = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends    = [DjangoFilterBackend]
    filterset_class    = UserFilter

    def get_queryset(self):
        return User.objects.all().order_by("id")


class AdminUserUpdateView(generics.UpdateAPIView):
    """Update user status. PATCH /api/admin/users/<id>/"""

    serializer_class   = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    http_method_names  = ["patch"]

    def get_queryset(self):
        return User.objects.all()


# ---------------------------------------------------------------------------
# BE-017 — Appointment overview view
# ---------------------------------------------------------------------------

class AdminAppointmentListView(generics.ListAPIView):
    """List all appointments. GET /api/admin/appointments/"""

    serializer_class   = AdminAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = AppointmentFilter
    ordering_fields    = ["date", "status"]
    ordering           = ["-date"]

    def get_queryset(self):
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
    """Return system-wide counts. GET /api/admin/stats/"""

    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
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


# ---------------------------------------------------------------------------
# Specialty CRUD views
# ---------------------------------------------------------------------------

class AdminSpecialtyListCreateView(generics.ListCreateAPIView):
    """List all specialties or create a new one.

    GET  /api/admin/specialties/  -- returns all specialties with doctor count
    POST /api/admin/specialties/  -- creates a new specialty
    """

    serializer_class   = SpecialtySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        # Annotate each specialty with how many doctors use it
        return (
            Specialty.objects
            .annotate(doctors_count=Count("doctorprofile"))
            .order_by("name")
        )


class AdminSpecialtyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single specialty.

    GET    /api/admin/specialties/<id>/
    PATCH  /api/admin/specialties/<id>/
    DELETE /api/admin/specialties/<id>/
    """

    serializer_class   = SpecialtySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    http_method_names  = ["get", "patch", "delete"]  # Disable PUT

    def get_queryset(self):
        return (
            Specialty.objects
            .annotate(doctors_count=Count("doctorprofile"))
            .all()
        )