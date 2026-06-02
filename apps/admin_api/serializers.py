# Third-party packages
from rest_framework import serializers

# Django
from django.contrib.auth import get_user_model

# Local / project imports
from apps.appointments.models import Appointment
from apps.doctors.models import DoctorProfile, Specialty

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
# BE-017 — Appointment overview serializers
# ---------------------------------------------------------------------------

class _AppointmentDoctorSerializer(serializers.ModelSerializer):
    name      = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "specialty", "image_url"]

    def get_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_specialty(self, obj) -> str | None:
        profile = getattr(obj, "doctor_profile", None)
        if profile and profile.specialty:
            return profile.specialty.name
        return None

    def get_image_url(self, obj) -> str | None:
        profile = getattr(obj, "doctor_profile", None)
        return profile.image_url if profile else None


class _AppointmentPatientSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email"]

    def get_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class AdminAppointmentSerializer(serializers.ModelSerializer):
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
    total_users         = serializers.IntegerField()
    total_doctors       = serializers.IntegerField()
    total_appointments  = serializers.IntegerField()
    pending_approvals   = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Specialty CRUD serializers
# ---------------------------------------------------------------------------

class SpecialtySerializer(serializers.ModelSerializer):
    """Full serializer for Specialty — used for list, create, update, delete."""

    # Annotated at query time in the view for performance
    doctors_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Specialty
        fields = ["id", "name", "description", "icon", "doctors_count"]
        read_only_fields = ["id", "doctors_count"]

    def validate_name(self, value):
        """Ensure specialty name is unique (case-insensitive), excluding self on update."""
        qs = Specialty.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A specialty with this name already exists.")
        return value