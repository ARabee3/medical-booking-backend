"""
Doctors app views.

Endpoints:
- GET /api/doctors/               → list approved doctors
- GET /api/doctors/<id>/          → single doctor profile
- GET /api/doctors/<id>/availability/?date=YYYY-MM-DD → free slots
- GET /api/doctors/<id>/availability/summary/?from=...&to=... → slot counts by date
- PATCH /api/doctors/me/update/   → update own profile
- POST /api/doctors/me/avatar/    → upload profile avatar
- DELETE /api/doctors/me/avatar/  → remove profile avatar
- GET /api/doctors/me/images/     → list own images
- POST /api/doctors/me/images/    → upload clinic/certificate image
- GET, PATCH, DELETE /api/doctors/me/images/<id>/ → manage single image
- GET /api/doctors/<id>/images/   → public list of doctor images
- GET /api/doctors/<id>/reviews/  → public list of doctor reviews
- GET /api/doctors/me/reviews/     → list own reviews (doctor)
"""

# Standard library
from datetime import date as dt_date

# Third-party packages
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

# Django
from django.db.models import Q, Count

# Local / project imports
from apps.appointments.serializers import ReviewReadSerializer
from apps.doctors.models import DoctorProfile, DoctorImage, Availability
from shared.pagination import StandardResultsSetPagination
from .serializers import (
    DoctorDetailSerializer,
    DoctorListSerializer,
    DoctorImageSerializer,
    DoctorImageUploadSerializer,
    DoctorProfileUpdateSerializer,
)
from .utils import delete_from_cloudinary


class DoctorListView(generics.ListAPIView):
    """List all approved and active doctors.

    Query parameters:
        specialty (str) -- case-insensitive exact match on specialty name
        search (str)    -- case-insensitive search on first or last name
    """

    serializer_class = DoctorListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = (
            DoctorProfile.objects
            .filter(user__is_active=True, user__is_approved=True)
            .select_related("user", "specialty")
        )

        # Filter by specialty name
        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialty__name__iexact=specialty)

        # Search by doctor name (first or last)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return qs.order_by("user__first_name", "user__last_name")


class DoctorDetailView(generics.RetrieveAPIView):
    """Retrieve a single approved doctor's profile."""

    serializer_class = DoctorDetailSerializer
    lookup_field = "pk"
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            DoctorProfile.objects
            .filter(user__is_active=True, user__is_approved=True)
            .select_related("user", "specialty")
            .prefetch_related("images")
        )

    def handle_exception(self, exc):
        """Override to return a cleaner 404 message."""
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            response.data = {"detail": "Doctor not found"}
        return response


class CurrentDoctorView(APIView):
    """Return the authenticated doctor's own profile.

    Used by the frontend doctor dashboard to resolve the logged-in doctor's ID.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            profile = DoctorProfile.objects.select_related("user", "specialty").prefetch_related("images").get(user=user)
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "You do not have a doctor profile."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DoctorDetailSerializer(profile)
        return Response(serializer.data)


class AvailabilityListView(APIView):
    """List available time slots for a doctor on a given date.

    This endpoint is public — patients browse slots before booking.

    Query parameters:
        date (str, required) -- YYYY-MM-DD format

    Response shape:
        {
            "doctor_id": 1,
            "date": "2026-01-20",
            "slots": [
                {"time": "09:00", "price": "150.00"},
                ...
            ]
        }
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int):
        # Validate the doctor exists and is active/approved
        try:
            doctor = (
                DoctorProfile.objects
                .filter(user__is_active=True, user__is_approved=True)
                .select_related("user")
                .get(pk=pk)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate date parameter
        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"date": ["This parameter is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            requested_date = dt_date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"date": ["Invalid date format. Use YYYY-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only serve slots for today or future dates
        if requested_date < dt_date.today():
            return Response(
                {
                    "doctor_id": doctor.id,
                    "date": date_str,
                    "slots": [],
                }
            )

        # Fetch unbooked slots for this doctor and date
        slots = (
            Availability.objects
            .filter(
                doctor=doctor,
                date=requested_date,
                is_booked=False,
            )
            .order_by("start_time")
        )

        slot_data = [
            {"time": s.start_time.strftime("%H:%M"), "price": str(s.price) if s.price else None}
            for s in slots
        ]

        return Response(
            {
                "doctor_id": doctor.id,
                "date": date_str,
                "slots": slot_data,
            }
        )


class AvailabilitySummaryView(APIView):
    """Summary of available slot counts per date for a doctor.

    Query parameters:
        from (str, required) -- YYYY-MM-DD
        to   (str, required) -- YYYY-MM-DD

    Response shape:
        {
            "doctor_id": 1,
            "from": "2026-06-01",
            "to": "2026-06-30",
            "slots_by_date": {
                "2026-06-05": 4,
                "2026-06-06": 3,
                ...
            },
            "total": 56
        }
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int):
        # Validate the doctor exists and is active/approved
        try:
            doctor = (
                DoctorProfile.objects
                .filter(user__is_active=True, user__is_approved=True)
                .select_related("user")
                .get(pk=pk)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate date range parameters
        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")

        if not from_str or not to_str:
            return Response(
                {"detail": "Both 'from' and 'to' parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from_date = dt_date.fromisoformat(from_str)
            to_date = dt_date.fromisoformat(to_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure from <= to
        if from_date > to_date:
            return Response(
                {"detail": "'from' date must be before or equal to 'to' date."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Clamp to today — past dates have no availability
        today = dt_date.today()
        if to_date < today:
            return Response(
                {
                    "doctor_id": doctor.id,
                    "from": from_str,
                    "to": to_str,
                    "slots_by_date": {},
                    "total": 0,
                }
            )

        if from_date < today:
            from_date = today

        # Aggregate available slot counts per date
        slot_counts = (
            Availability.objects
            .filter(
                doctor=doctor,
                date__gte=from_date,
                date__lte=to_date,
                is_booked=False,
            )
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        slots_by_date = {}
        total = 0
        for entry in slot_counts:
            date_key = entry["date"].isoformat()
            slots_by_date[date_key] = entry["count"]
            total += entry["count"]

        return Response(
            {
                "doctor_id": doctor.id,
                "from": from_str,
                "to": to_str,
                "slots_by_date": slots_by_date,
                "total": total,
            }
        )


class CurrentDoctorUpdateView(APIView):
    """PATCH /api/doctors/me/update/ — update own profile (bio, specialty, phone)."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = user.doctor_profile
        serializer = DoctorProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DoctorDetailSerializer(profile).data)


class AvatarUploadView(APIView):
    """POST /api/doctors/me/avatar/ — upload profile avatar to Cloudinary."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can upload an avatar."},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = user.doctor_profile
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"image": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.doctors.utils import upload_to_cloudinary

        if profile.profile_public_id:
            delete_from_cloudinary(profile.profile_public_id)

        image_url, public_id = upload_to_cloudinary(image, folder=f"doctors/{profile.id}/avatar")

        profile.image_url = image_url
        profile.profile_public_id = public_id
        profile.save(update_fields=["image_url", "profile_public_id"])

        return Response(DoctorDetailSerializer(profile).data, status=status.HTTP_200_OK)


class AvatarDeleteView(APIView):
    """DELETE /api/doctors/me/avatar/ — remove profile avatar, reset to default."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can manage their avatar."},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = user.doctor_profile
        if profile.profile_public_id:
            delete_from_cloudinary(profile.profile_public_id)
        profile.image_url = ""
        profile.profile_public_id = ""
        profile.save(update_fields=["image_url", "profile_public_id"])
        return Response(DoctorDetailSerializer(profile).data, status=status.HTTP_200_OK)


class DoctorImageListView(APIView):
    """GET /api/doctors/me/images/ — list own images.
    POST /api/doctors/me/images/ — upload a new clinic/certificate image.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = user.doctor_profile
        qs = profile.images.all()
        kind = request.query_params.get("kind")
        if kind in ("CLINIC", "CERTIFICATE"):
            qs = qs.filter(kind=kind)
        serializer = DoctorImageSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can upload images."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DoctorImageUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        image = serializer.save()
        return Response(DoctorImageSerializer(image).data, status=status.HTTP_201_CREATED)


class DoctorImageDetailView(APIView):
    """GET, PATCH, DELETE /api/doctors/me/images/<id>/ — manage a single image."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        obj = DoctorImage.objects.select_related("doctor", "doctor__user").get(pk=pk)
        if obj.doctor.user != self.request.user:
            raise DoctorImage.DoesNotExist
        return obj

    def get(self, request, pk):
        try:
            image = self.get_object(pk)
        except DoctorImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DoctorImageSerializer(image).data)

    def patch(self, request, pk):
        try:
            image = self.get_object(pk)
        except DoctorImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
        allowed_fields = {"caption", "order"}
        for field in allowed_fields:
            if field in request.data:
                setattr(image, field, request.data[field])
        image.save(update_fields=["caption", "order"])
        return Response(DoctorImageSerializer(image).data)

    def delete(self, request, pk):
        try:
            image = self.get_object(pk)
        except DoctorImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
        delete_from_cloudinary(image.public_id)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicDoctorImagesView(APIView):
    """GET /api/doctors/<id>/images/ — public list of a doctor's images."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            doctor = (
                DoctorProfile.objects
                .filter(user__is_active=True, user__is_approved=True)
                .get(pk=pk)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = doctor.images.all()
        kind = request.query_params.get("kind")
        if kind in ("CLINIC", "CERTIFICATE"):
            qs = qs.filter(kind=kind)
        serializer = DoctorImageSerializer(qs, many=True)
        return Response(serializer.data)


class DoctorReviewsView(APIView):
    """GET /api/doctors/<id>/reviews/ — public list of a doctor's reviews."""

    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get(self, request, pk):
        try:
            doctor = (
                DoctorProfile.objects
                .filter(user__is_active=True, user__is_approved=True)
                .get(pk=pk)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = doctor.reviews.select_related("patient").all()
        serializer = ReviewReadSerializer(qs, many=True)
        return Response(serializer.data)


class CurrentDoctorReviewsView(APIView):
    """GET /api/doctors/me/reviews/ — list reviews for the current doctor."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "DOCTOR":
            return Response(
                {"detail": "Only doctors can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            profile = user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return Response(
                {"detail": "You do not have a doctor profile."},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = profile.reviews.select_related("patient").all()
        serializer = ReviewReadSerializer(qs, many=True)
        return Response(serializer.data)
