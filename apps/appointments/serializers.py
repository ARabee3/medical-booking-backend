"""
Appointments app serializers.

- AppointmentDoctorSerializer : Nested doctor info inside appointment responses.
- AppointmentReadSerializer   : Full appointment output shape (GET list/detail).
- AppointmentWriteSerializer  : Patient booking input validation (POST).
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.appointments.models import Appointment
from apps.appointments.services import book_appointment

User = get_user_model()


class AppointmentDoctorSerializer(serializers.Serializer):
    """Read-only nested doctor object embedded in appointment responses.

    The `id` field returns DoctorProfile.id for consistency with the
    GET /api/doctors/ endpoint used by the frontend.
    """

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    def get_id(self, obj):
        """Return DoctorProfile.id (not User.id) for frontend navigation."""
        try:
            return obj.doctor_profile.id
        except AttributeError:
            return None

    def get_name(self, obj):
        """Return formatted display name."""
        return f"Dr. {obj.first_name} {obj.last_name}"

    def get_specialty(self, obj):
        """Return specialty name or None."""
        try:
            specialty = obj.doctor_profile.specialty
            return specialty.name if specialty else None
        except AttributeError:
            return None

    def get_image_url(self, obj):
        """Return image URL or None if unset."""
        try:
            return obj.doctor_profile.image_url or None
        except AttributeError:
            return None


class AppointmentReadSerializer(serializers.ModelSerializer):
    """Output serializer for appointment list and post-booking responses.

    Produces the exact shape defined in docs/API_CONTRACT.md §Appointments.
    """

    doctor = AppointmentDoctorSerializer(read_only=True)
    time = serializers.TimeField(format="%H:%M", read_only=True)
    date = serializers.DateField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "doctor", "date", "time", "status", "notes", "created_at"]
        read_only_fields = ["id", "doctor", "date", "time", "status", "notes", "created_at"]


class AppointmentWriteSerializer(serializers.Serializer):
    """Input serializer for patient booking — POST /api/appointments/.

    Accepts doctor_id (User.id), date (YYYY-MM-DD), and time (HH:MM).
    All booking business logic is delegated to services.book_appointment().
    """

    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    time = serializers.TimeField(input_formats=["%H:%M", "%H:%M:%S"])

    def validate(self, attrs):
        """Resolve doctor_id to a User instance; fail fast with clear error."""
        try:
            doctor = User.objects.get(
                id=attrs["doctor_id"],
                role="DOCTOR",
                is_active=True,
                is_approved=True,
            )
        except User.DoesNotExist:
            raise ValidationError({"doctor_id": ["Doctor not found or not available."]})

        # Attach resolved object so create() avoids a second DB hit
        attrs["doctor"] = doctor
        return attrs

    def create(self, validated_data):
        """Delegate to the booking service — no logic lives in the serializer."""
        return book_appointment(
            patient=self.context["request"].user,
            doctor=validated_data["doctor"],
            date=validated_data["date"],
            time=validated_data["time"],
        )
