# Standard library
from datetime import datetime

# Django
from django.contrib.auth import get_user_model
from django.utils import timezone

# Third-party packages
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# Local / project imports
from apps.appointments.models import Appointment
from apps.appointments.services import book_appointment
from apps.doctors.models import Availability, DoctorProfile

User = get_user_model()


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for doctor availability slots.

    Read:  exposes doctor_id (DoctorProfile.id) so the frontend can
           invalidate the correct query cache.
    Write: doctor is resolved from the authenticated user (or supplied
           by an admin) in validate().
    """

    doctor_id = serializers.IntegerField(source="doctor.id", read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.all(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Availability
        fields = [
            "id",
            "doctor_id",
            "doctor",
            "date",
            "start_time",
            "end_time",
            "is_booked",
        ]
        read_only_fields = ["id", "is_booked", "doctor_id"]

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Availability date must be today or in the future."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request = self.context.get("request")
        date = attrs["date"]
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]

        if end_time <= start_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )

        slot_naive = datetime.combine(date, start_time)
        now = timezone.now()

        if timezone.is_aware(now):
            slot_dt = timezone.make_aware(slot_naive)
        else:
            slot_dt = slot_naive

        if slot_dt <= now:
            raise serializers.ValidationError(
                {"start_time": "The slot date and start time must be in the future."}
            )

        doctor = self._resolve_doctor(attrs, request)
        attrs["doctor"] = doctor

        overlapping_qs = Availability.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if self.instance:
            overlapping_qs = overlapping_qs.exclude(pk=self.instance.pk)

        if overlapping_qs.exists():
            raise serializers.ValidationError(
                {
                    "start_time": (
                        "This slot overlaps with an existing availability slot "
                        "for the same doctor on the same date."
                    )
                }
            )

        return attrs

    def _resolve_doctor(self, attrs, request):
        user = getattr(request, "user", None)

        if user and user.role == "DOCTOR":
            profile = getattr(user, "doctor_profile", None)
            if profile is None:
                raise serializers.ValidationError(
                    "Your account does not have an associated doctor profile."
                )
            return profile

        if user and user.role == "ADMIN":
            doctor = attrs.get("doctor")
            if doctor is None:
                raise serializers.ValidationError(
                    {
                        "doctor": "Admin must supply a doctor ID when creating an availability slot."
                    }
                )
            return doctor

        raise serializers.ValidationError(
            "Only doctors and admins can create availability slots."
        )


class AppointmentDoctorSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    def get_id(self, obj):
        try:
            return obj.doctor_profile.id
        except AttributeError:
            return None

    def get_name(self, obj):
        return f"Dr. {obj.first_name} {obj.last_name}"

    def get_specialty(self, obj):
        try:
            specialty = obj.doctor_profile.specialty
            return specialty.name if specialty else None
        except AttributeError:
            return None

    def get_image_url(self, obj):
        try:
            return obj.doctor_profile.image_url or None
        except AttributeError:
            return None


class AppointmentReadSerializer(serializers.ModelSerializer):
    doctor = AppointmentDoctorSerializer(read_only=True)
    time = serializers.TimeField(format="%H:%M", read_only=True)
    date = serializers.DateField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "doctor", "date", "time", "status", "notes", "created_at"]
        read_only_fields = ["id", "doctor", "date", "time", "status", "notes", "created_at"]


class AppointmentWriteSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    time = serializers.TimeField(input_formats=["%H:%M", "%H:%M:%S"])

    def validate(self, attrs):
        from apps.doctors.models import DoctorProfile
        try:
            profile = DoctorProfile.objects.select_related("user").get(
                id=attrs["doctor_id"],
                user__role="DOCTOR",
                user__is_active=True,
                user__is_approved=True,
            )
            doctor = profile.user
        except DoctorProfile.DoesNotExist:
            raise ValidationError({"doctor_id": ["Doctor not found or not available."]})

        attrs["doctor"] = doctor
        attrs["doctor_profile"] = profile
        return attrs

    def create(self, validated_data):
        return book_appointment(
            patient=self.context["request"].user,
            doctor=validated_data["doctor"],
            date=validated_data["date"],
            time=validated_data["time"],
        )


class AppointmentUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["CANCELLED"], required=False)
    date = serializers.DateField(required=False)
    time = serializers.TimeField(input_formats=["%H:%M", "%H:%M:%S"], required=False)

    def validate(self, attrs):
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
    id = serializers.IntegerField(source="pk")
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class DoctorAppointmentReadSerializer(serializers.ModelSerializer):
    patient = AppointmentPatientSerializer(read_only=True)
    time = serializers.TimeField(format="%H:%M", read_only=True)
    date = serializers.DateField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "patient", "date", "time", "status", "notes", "created_at"]
        read_only_fields = ["id", "patient", "date", "time", "status", "notes", "created_at"]


class DoctorAppointmentUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=["CONFIRMED", "CANCELLED"])
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = ["status", "notes"]
