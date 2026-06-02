"""
Pytest configuration and shared fixtures.

Provides reusable fixtures for all test modules across the project.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.users.models import PatientProfile

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def patient_user(db):
    """Create and return a verified patient user with PatientProfile."""
    user = User.objects.create_user(
        email="patient@test.com",
        password="testpass123",
        first_name="John",
        last_name="Doe",
        role="PATIENT",
        is_approved=True,
    )
    PatientProfile.objects.create(user=user)
    return user


@pytest.fixture
def doctor_user(db):
    """Create and return an approved doctor user with DoctorProfile."""
    from apps.doctors.models import DoctorProfile, Specialty
    user = User.objects.create_user(
        email="doctor@test.com",
        password="testpass123",
        first_name="Sarah",
        last_name="Chen",
        role="DOCTOR",
        is_approved=True,
    )
    specialty = Specialty.objects.create(name="Cardiology")
    DoctorProfile.objects.create(user=user, specialty=specialty)
    return user


@pytest.fixture
def unapproved_doctor(db):
    """Create and return a doctor user pending approval."""
    return User.objects.create_user(
        email="pending@test.com",
        password="testpass123",
        first_name="New",
        last_name="Doctor",
        role="DOCTOR",
        is_approved=False,
    )


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        first_name="Admin",
        last_name="User",
        role="ADMIN",
        is_approved=True,
    )
