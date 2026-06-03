from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.appointments.models import Appointment, Review
from apps.appointments.serializers import (
    AppointmentReadSerializer,
    AppointmentUpdateSerializer,
    AppointmentWriteSerializer,
    AvailabilitySerializer,
    DoctorAppointmentReadSerializer,
    DoctorAppointmentUpdateSerializer,
    ReviewReadSerializer,
    ReviewWriteSerializer,
    ReviewUpdateSerializer,
)
from apps.doctors.models import Availability
from shared.pagination import StandardResultsSetPagination
from shared.permissions import IsDoctor, IsPatient


class AvailabilityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Availability.objects.select_related(
            "doctor",
            "doctor__user",
            "doctor__specialty",
        ).all()

        doctor_id = self.request.query_params.get("doctor_id")
        date = self.request.query_params.get("date")
        is_booked = self.request.query_params.get("is_booked")

        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        elif self.request.user.role == "DOCTOR":
            # If no explicit doctor_id, doctors only see their own slots
            profile = getattr(self.request.user, "doctor_profile", None)
            if profile:
                qs = qs.filter(doctor=profile)

        if date:
            qs = qs.filter(date=date)

        if is_booked is not None:
            qs = qs.filter(is_booked=is_booked.lower() == "true")

        return qs.order_by("date", "start_time")

    def _assert_can_write(self):
        if self.request.user.role not in ("DOCTOR", "ADMIN"):
            raise PermissionDenied(
                "Only doctors and admins can manage availability slots."
            )

    def perform_create(self, serializer):
        self._assert_can_write()
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_can_write()

        if instance.is_booked:
            raise ValidationError(
                {"detail": "Cannot delete a slot that is already booked by a patient."}
            )

        user = self.request.user
        if user.role == "DOCTOR":
            profile = getattr(user, "doctor_profile", None)
            if profile is None or instance.doctor_id != profile.pk:
                raise PermissionDenied(
                    "You can only delete your own availability slots."
                )

        instance.delete()


class PatientAppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AppointmentWriteSerializer
        return AppointmentReadSerializer

    def get_queryset(self):
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related(
                "doctor",
                "doctor__doctor_profile",
                "doctor__doctor_profile__specialty",
            )
        )

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        appointment = write_serializer.save()

        read_serializer = AppointmentReadSerializer(
            appointment,
            context={"request": request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class PatientAppointmentDetailView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    serializer_class = AppointmentUpdateSerializer

    def get_queryset(self):
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related(
                "doctor",
                "doctor__doctor_profile",
                "doctor__doctor_profile__specialty",
            )
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        from apps.appointments.services import cancel_appointment, reschedule_appointment

        validated_data = serializer.validated_data

        if validated_data.get("status") == "CANCELLED":
            appointment = cancel_appointment(appointment=instance)
        else:
            appointment = reschedule_appointment(
                appointment=instance,
                new_date=validated_data["date"],
                new_time=validated_data["time"],
            )

        read_serializer = AppointmentReadSerializer(
            appointment,
            context={"request": request},
        )
        return Response(read_serializer.data)


class DoctorAppointmentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = DoctorAppointmentReadSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return (
            Appointment.objects.filter(doctor=self.request.user)
            .select_related("patient")
            .order_by("-date", "-time")
        )


class DoctorAppointmentDetailView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = DoctorAppointmentUpdateSerializer

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user).select_related(
            "patient"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        if validated_data.get("status") == "CANCELLED":
            from apps.appointments.services import cancel_appointment

            appointment = cancel_appointment(appointment=instance)

            if "notes" in validated_data:
                appointment.notes = validated_data["notes"]
                appointment.save(update_fields=["notes"])
        else:
            appointment = serializer.save()

        read_serializer = DoctorAppointmentReadSerializer(
            appointment,
            context={"request": request},
        )
        return Response(read_serializer.data)


class CreateReviewView(APIView):
    """POST /api/appointments/<pk>/review/ — create a review for a completed appointment."""

    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request, pk):
        serializer = ReviewWriteSerializer(
            data=request.data,
            context={"request": request, "appointment_pk": pk},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewReadSerializer(review).data, status=status.HTTP_201_CREATED)


class AppointmentReviewView(APIView):
    """GET /api/appointments/<pk>/review/ — get review for a specific appointment."""

    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, patient=request.user)
        except Appointment.DoesNotExist:
            return Response(
                {"detail": "Appointment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            review = appointment.review
        except Review.DoesNotExist:
            return Response(
                {"detail": "No review found for this appointment."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ReviewReadSerializer(review).data)


class ReviewDetailView(APIView):
    """PATCH /api/reviews/<pk>/ — edit own review.
    DELETE /api/reviews/<pk>/ — delete own review.
    """

    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_object(self, pk):
        try:
            review = Review.objects.select_related("patient").get(pk=pk)
        except Review.DoesNotExist:
            raise PermissionDenied("Review not found.")
        if review.patient != self.request.user:
            raise PermissionDenied("You can only manage your own reviews.")
        return review

    def patch(self, request, pk):
        review = self.get_object(pk)
        serializer = ReviewUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.rating = serializer.validated_data["rating"]
        review.comment = serializer.validated_data.get("comment", "")
        review.save(update_fields=["rating", "comment", "updated_at"])
        return Response(ReviewReadSerializer(review).data)

    def delete(self, request, pk):
        review = self.get_object(pk)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
