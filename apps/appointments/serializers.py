# Standard library
from datetime import datetime

# Third-party packages
from rest_framework import serializers

# Django
from django.utils import timezone

# Local / project imports
from apps.doctors.models import Availability
from apps.doctors.models import DoctorProfile


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for doctor availability slots.

    Handles creation validation:
        - Slot must be strictly in the future.
        - No overlapping slots for the same doctor on the same date.

    Doctor assignment:
        - DOCTOR role -> auto-assigned from request.user.doctor_profile.
        - ADMIN role  -> must supply doctor in the payload.
    """

    # Writable for admins (they supply a doctor_id); auto-set for doctors.
    # required=False because doctors don't send it — _resolve_doctor fills it in.
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.all(),
        required=False,
    )

    class Meta:
        model  = Availability
        fields = [
            "id",
            "doctor",
            "date",
            "start_time",
            "end_time",
            "is_booked",
        ]
        read_only_fields = ["id", "is_booked"]

    # ------------------------------------------------------------------
    # Field-level validation
    # ------------------------------------------------------------------

    def validate_date(self, value):
        """Reject dates strictly in the past."""
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Availability date must be today or in the future."
            )
        return value

    # ------------------------------------------------------------------
    # Object-level validation
    # ------------------------------------------------------------------

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request    = self.context.get("request")
        date       = attrs["date"]
        start_time = attrs["start_time"]
        end_time   = attrs["end_time"]

        # 1. end_time must be strictly after start_time ------------------
        if end_time <= start_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )

        # 2. The slot (date + start_time) must be strictly in the future -
        slot_naive = datetime.combine(date, start_time)
        now        = timezone.now()

        # Keep both naive or both aware to compare safely
        if timezone.is_aware(now):
            slot_dt = timezone.make_aware(slot_naive)
        else:
            slot_dt = slot_naive

        if slot_dt <= now:
            raise serializers.ValidationError(
                {"start_time": "The slot date and start time must be in the future."}
            )

        # 3. Resolve which DoctorProfile this slot belongs to ------------
        doctor      = self._resolve_doctor(attrs, request)
        attrs["doctor"] = doctor

        # 4. Overlap check on the same doctor + date ---------------------
        # Two time ranges overlap when: start_A < end_B AND end_A > start_B
        overlapping_qs = Availability.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,   # existing_start < new_end
            end_time__gt=start_time,   # existing_end   > new_start
        )

        # Exclude current instance on partial updates (PATCH)
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_doctor(self, attrs, request):
        """Return the correct DoctorProfile for this availability slot.

        Args:
            attrs:   Validated field data from the serializer.
            request: The DRF request from serializer context.

        Returns:
            DoctorProfile: The resolved doctor instance.

        Raises:
            ValidationError: If the doctor cannot be determined.
        """
        user = getattr(request, "user", None)

        if user and user.role == "DOCTOR":
            # Doctors always create slots for themselves — ignore any doctor in payload
            profile = getattr(user, "doctor_profile", None)
            if profile is None:
                raise serializers.ValidationError(
                    "Your account does not have an associated doctor profile."
                )
            return profile

        if user and user.role == "ADMIN":
            # Admins must explicitly specify which doctor the slot belongs to
            doctor = attrs.get("doctor")
            if doctor is None:
                raise serializers.ValidationError(
                    {"doctor": "Admin must supply a doctor ID when creating an availability slot."}
                )
            return doctor

        raise serializers.ValidationError(
            "Only doctors and admins can create availability slots."
        )