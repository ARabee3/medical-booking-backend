# Third-party packages
from rest_framework import serializers

# Django
from django.contrib.auth import get_user_model

# Local / project imports
from apps.appointments.models import Appointment

User = get_user_model()


# ---------------------------------------------------------------------------
# BE-016 — User management serializer
# ---------------------------------------------------------------------------

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management.

    Read fields: all user info.
    Writable fields: is_active, is_approved only.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_approved",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
        ]


# ---------------------------------------------------------------------------
# BE-017 — Appointment overview serializers (nested, no cross-app imports)
# ---------------------------------------------------------------------------

class _AppointmentDoctorSerializer(serializers.ModelSerializer):
    """Lightweight doctor representation nested inside AdminAppointmentSerializer.

    Declared here (not imported from apps.doctors) to avoid circular imports.
    Pulls specialty and image_url from the related DoctorProfile via properties.
    """

    name      = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "specialty", "image_url"]

    def get_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_specialty(self, obj) -> str | None:
        """Traverse user → doctor_profile → specialty safely."""
        profile = getattr(obj, "doctor_profile", None)
        if profile and profile.specialty:
            return profile.specialty.name
        return None

    def get_image_url(self, obj) -> str | None:
        profile = getattr(obj, "doctor_profile", None)
        return profile.image_url if profile else None


class _AppointmentPatientSerializer(serializers.ModelSerializer):
    """Lightweight patient representation nested inside AdminAppointmentSerializer."""

    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email"]

    def get_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class AdminAppointmentSerializer(serializers.ModelSerializer):
    """Full appointment serializer for the admin overview endpoint.

    Returns nested doctor and patient objects matching the API contract shape.
    All fields are read-only — admins observe, not modify, via this endpoint.
    """

    doctor  = _AppointmentDoctorSerializer(read_only=True)
    patient = _AppointmentPatientSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor",
            "patient",
            "date",
            "time",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# BE-018 — Dashboard stats serializer
# ---------------------------------------------------------------------------

class AdminStatsSerializer(serializers.Serializer):
    """Flat serializer for the admin dashboard stats endpoint.

    Validates the exact shape documented in the API contract.
    """

    total_users         = serializers.IntegerField()
    total_doctors       = serializers.IntegerField()
    total_appointments  = serializers.IntegerField()
    pending_approvals   = serializers.IntegerField()