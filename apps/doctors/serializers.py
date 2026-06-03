"""
Doctors app serializers.

Handles serialization of doctor profiles, specialties, and availability slots.
"""

# Django
from django.db.models import Avg, Count

# Third-party packages
from rest_framework import serializers

# Local / project imports
from apps.doctors.models import DoctorProfile, DoctorImage, Specialty, Availability


class SpecialtySerializer(serializers.ModelSerializer):
    """Serializer for the Specialty model."""

    class Meta:
        model = Specialty
        fields = ["id", "name", "description", "icon"]
        read_only_fields = ["id"]


class DoctorListSerializer(serializers.ModelSerializer):
    """Serializer for listing approved doctors.

    Exposes a flat shape matching the frontend Doctor type:
    { id, user_id, name, email, specialty, bio, image_url, is_active, average_rating, review_count }
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    specialty = serializers.CharField(source="specialty.name", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

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
            "average_rating",
            "review_count",
        ]
        read_only_fields = fields

    def get_name(self, obj: DoctorProfile) -> str:
        """Return the doctor's display name with title."""
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"

    def get_average_rating(self, obj: DoctorProfile):
        agg = obj.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        if agg["count"] == 0:
            return None
        return round(agg["avg"] or 0, 1)

    def get_review_count(self, obj: DoctorProfile):
        return obj.reviews.count()


class DoctorDetailSerializer(DoctorListSerializer):
    """Serializer for a single doctor's full profile.

    Reuses DoctorListSerializer fields; can be extended later with
    nested availability or statistics if needed.
    """

    images = serializers.SerializerMethodField(read_only=True)

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
            "average_rating",
            "review_count",
            "images",
        ]
        read_only_fields = fields

    def get_images(self, obj: DoctorProfile) -> list[dict]:
        """Return clinic and certificate images."""
        return [
            {
                "id": img.id,
                "image_url": img.image_url,
                "public_id": img.public_id,
                "kind": img.kind,
                "caption": img.caption,
                "order": img.order,
                "created_at": img.created_at.isoformat(),
            }
            for img in obj.images.all()
        ]


class DoctorImageSerializer(serializers.ModelSerializer):
    """Serializer for doctor-uploaded images (clinic / certificate)."""

    doctor_id = serializers.IntegerField(source="doctor.id", read_only=True)

    class Meta:
        model = DoctorImage
        fields = [
            "id",
            "doctor_id",
            "image_url",
            "public_id",
            "kind",
            "caption",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "doctor_id", "image_url", "public_id", "created_at"]


class DoctorImageUploadSerializer(serializers.Serializer):
    """Serializer for uploading a new doctor image (clinic or certificate)."""

    kind = serializers.ChoiceField(choices=DoctorImage.KIND_CHOICES)
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    image = serializers.ImageField(write_only=True)

    def create(self, validated_data):
        from apps.doctors.utils import upload_to_cloudinary

        image = validated_data.pop("image")
        kind = validated_data["kind"]
        caption = validated_data.get("caption", "")
        doctor = self.context["request"].user.doctor_profile

        image_url, public_id = upload_to_cloudinary(image, folder=f"doctors/{doctor.id}/{kind.lower()}")

        return DoctorImage.objects.create(
            doctor=doctor,
            image_url=image_url,
            public_id=public_id,
            kind=kind,
            caption=caption,
        )


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a doctor's own profile."""

    specialty = serializers.CharField(source="specialty.name", required=False, allow_blank=True)

    class Meta:
        model = DoctorProfile
        fields = ["bio", "specialty", "phone"]

    def update(self, instance, validated_data):
        specialty_data = validated_data.pop("specialty", None)
        if specialty_data:
            specialty_name = specialty_data.get("name")
            if specialty_name:
                specialty = Specialty.objects.filter(name=specialty_name).first()
                if specialty:
                    instance.specialty = specialty
        instance = super().update(instance, validated_data)
        if specialty_data:
            instance.save(update_fields=["specialty"])
        return instance


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
            "price",
            "is_booked",
        ]
        read_only_fields = ["id", "doctor_id", "is_booked"]
