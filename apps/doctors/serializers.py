"""
Doctors app serializers.

Handles serialization of doctor profiles, specialties, and availability slots.
"""

# Third-party packages
from rest_framework import serializers

# Local / project imports
from apps.doctors.models import DoctorProfile, Specialty, Availability


class SpecialtySerializer(serializers.ModelSerializer):
    """Serializer for the Specialty model."""

    class Meta:
        model = Specialty
        fields = ["id", "name", "description", "icon"]
        read_only_fields = ["id"]


class DoctorListSerializer(serializers.ModelSerializer):
    """Serializer for listing approved doctors.

    Exposes a flat shape matching the frontend Doctor type:
    { id, user_id, name, email, specialty, bio, image_url, is_active }
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    specialty = serializers.CharField(source="specialty.name", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "user_id",
            "name",
            "email",
            "specialty",
            "bio",
            "image_url",
            "is_active",
        ]
        read_only_fields = fields

    def get_name(self, obj: DoctorProfile) -> str:
        """Return the doctor's display name with title."""
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"


class DoctorDetailSerializer(DoctorListSerializer):
    """Serializer for a single doctor's full profile.

    Reuses DoctorListSerializer fields; can be extended later with
    nested availability or statistics if needed.
    """

    class Meta(DoctorListSerializer.Meta):
        pass


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    """Serializer for doctor availability slots.

    Used by doctor-facing schedule management endpoints.
    """

    doctor_id = serializers.IntegerField(source="doctor.id", read_only=True)

    class Meta:
        model = Availability
        fields = [
            "id",
            "doctor_id",
            "date",
            "start_time",
            "end_time",
            "is_booked",
        ]
        read_only_fields = ["id", "doctor_id", "is_booked"]
