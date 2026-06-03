"""
Doctors app models.

Models: Specialty, DoctorProfile, Availability
See docs/DATABASE_ARCHITECTURE.md for full schema.
"""

from django.db import models
from django.conf import settings


class Specialty(models.Model):
    """Medical specialty (e.g., Cardiology, Dermatology)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "specialties_specialty"
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    """Extended profile for doctors."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    bio = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    profile_public_id = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "doctors_doctorprofile"

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"


class DoctorImage(models.Model):
    """Clinic or certificate image uploaded by a doctor."""

    KIND_CHOICES = [
        ("CLINIC", "Clinic"),
        ("CERTIFICATE", "Certificate"),
    ]

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField()
    public_id = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    caption = models.CharField(max_length=200, blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "doctors_doctorimage"
        ordering = ["kind", "order", "created_at"]

    def __str__(self):
        return f"{self.kind} - {self.doctor} ({self.caption or self.public_id})"


class Availability(models.Model):
    """Time slot offered by a doctor."""

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="availabilities",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Consultation price for this slot in local currency.",
    )
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "doctors_availability"
        verbose_name_plural = "Availabilities"
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F("start_time")),
                name="end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["doctor", "date"]),
            models.Index(fields=["is_booked"]),
        ]

    def __str__(self):
        return f"{self.doctor} — {self.date} {self.start_time}-{self.end_time}"
