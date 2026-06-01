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


class AppointmentUpdateSerializer(serializers.Serializer):
    """Input serializer for patient modifications — PATCH /api/appointments/:id/.

    Accepts status="CANCELLED" to cancel, or date/time to reschedule.
    """

    status = serializers.ChoiceField(choices=["CANCELLED"], required=False)
    date = serializers.DateField(required=False)
    time = serializers.TimeField(input_formats=["%H:%M", "%H:%M:%S"], required=False)

    def validate(self, attrs):
        """Ensure either cancellation or rescheduling data is provided."""
        has_status = "status" in attrs
        has_reschedule = "date" in attrs and "time" in attrs

        if not has_status and not has_reschedule:
            raise ValidationError(
                "Provide status='CANCELLED' to cancel, or both date and time to reschedule."
            )
            
        if has_status and has_reschedule:
             raise ValidationError(
                "Cannot cancel and reschedule in the same request."
            )

        return attrs


class AppointmentPatientSerializer(serializers.Serializer):
    """Read-only nested patient object embedded in doctor appointment responses."""

    id = serializers.IntegerField(source="pk")
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()

    def get_name(self, obj):
        """Return formatted display name."""
        return f"{obj.first_name} {obj.last_name}"


class DoctorAppointmentReadSerializer(serializers.ModelSerializer):
    """Output serializer for doctor appointment list.

    Produces the exact shape defined in docs/API_CONTRACT.md §Doctor Endpoints.
    """

    patient = AppointmentPatientSerializer(read_only=True)
    time = serializers.TimeField(format="%H:%M", read_only=True)
    date = serializers.DateField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "patient", "date", "time", "status", "notes", "created_at"]
        read_only_fields = ["id", "patient", "date", "time", "status", "notes", "created_at"]


class DoctorAppointmentUpdateSerializer(serializers.ModelSerializer):
    """Input serializer for doctor modifications — PATCH /api/doctor/appointments/:id/.

    Accepts status="CONFIRMED" or "CANCELLED" and optional notes.
    """

    status = serializers.ChoiceField(choices=["CONFIRMED", "CANCELLED"])
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = ["status", "notes"]
