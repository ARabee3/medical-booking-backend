"""
Custom User model for medical-booking-backend.

Extends AbstractUser to use email as the primary identifier
and adds role-based fields (ADMIN, DOCTOR, PATIENT).

See docs/DATABASE_ARCHITECTURE.md for full schema.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with email-based login and role system."""

    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("DOCTOR", "Doctor"),
        ("PATIENT", "Patient"),
    ]

    username = None  # Use email instead of username
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]


class PatientProfile(models.Model):
    """Extended profile for patients."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"PatientProfile({self.user.email})"

    class Meta:
        db_table = "patients_patientprofile"
