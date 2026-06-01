# Third-party packages
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

# Django
from django.utils import timezone

# Local / project imports
from apps.appointments.models import Availability
from apps.appointments.serializers import AvailabilitySerializer


class AvailabilityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for doctor availability slot management.

    Allowed actions:
        LIST    GET  /availability/          -- public, supports filtering
        CREATE  POST /availability/          -- DOCTOR or ADMIN only
        DESTROY DELETE /availability/<id>/  -- DOCTOR or ADMIN only

    Filtering (via query params, no django-filter dependency needed):
        ?doctor_id=<int>   -- slots for a specific doctor
        ?date=YYYY-MM-DD   -- slots on a specific date
        ?is_booked=true/false -- filter by booking status
    """

    serializer_class   = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    # ------------------------------------------------------------------
    # Queryset — supports manual query param filtering
    # ------------------------------------------------------------------

    def get_queryset(self):
        """Return availability slots, optionally filtered by query params."""
        qs = Availability.objects.select_related(
            "doctor",
            "doctor__user",
            "doctor__specialty",
        ).all()

        doctor_id = self.request.query_params.get("doctor_id")
        date      = self.request.query_params.get("date")
        is_booked = self.request.query_params.get("is_booked")

        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)

        if date:
            qs = qs.filter(date=date)

        if is_booked is not None:
            # Accept 'true'/'false' strings from query params
            qs = qs.filter(is_booked=is_booked.lower() == "true")

        return qs.order_by("date", "start_time")

    # ------------------------------------------------------------------
    # Permission guard — write actions restricted to DOCTOR / ADMIN
    # ------------------------------------------------------------------

    def _assert_can_write(self):
        """Raise 403 if the requesting user is not a DOCTOR or ADMIN.

        Called explicitly in create and destroy since we need per-action
        permission logic beyond what a single permission_class can express.
        """
        if self.request.user.role not in ("DOCTOR", "ADMIN"):
            raise PermissionDenied(
                "Only doctors and admins can manage availability slots."
            )

    # ------------------------------------------------------------------
    # Create — auto-assign doctor for DOCTOR role
    # ------------------------------------------------------------------

    def perform_create(self, serializer):
        """Save the new slot.

        Doctor assignment is already resolved inside AvailabilitySerializer.validate()
        and stored in validated_data['doctor'], so we just call save() here.
        """
        self._assert_can_write()
        serializer.save()

    # ------------------------------------------------------------------
    # Destroy — block deletion of booked slots; enforce ownership for doctors
    # ------------------------------------------------------------------

    def perform_destroy(self, instance):
        """Delete a slot after validating it is not booked.

        Additional ownership check: a DOCTOR can only delete their own slots.
        An ADMIN can delete any slot.
        """
        self._assert_can_write()

        # Block deletion if a patient has already booked the slot
        if instance.is_booked:
            raise ValidationError(
                {"detail": "Cannot delete a slot that is already booked by a patient."}
            )

        # Doctors can only delete their own slots
        user = self.request.user
        if user.role == "DOCTOR":
            profile = getattr(user, "doctor_profile", None)
            if profile is None or instance.doctor_id != profile.pk:
                raise PermissionDenied(
                    "You can only delete your own availability slots."
                )

        instance.delete()