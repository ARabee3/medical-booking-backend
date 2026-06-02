"""
Users app tests.

Tests for authentication endpoints: register, login, token refresh.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apps.users.models import PatientProfile

User = get_user_model()


# ==========================
# Registration Tests
# ==========================

@pytest.mark.django_db
class TestRegistration:
    """Tests for POST /api/register/."""

    def test_register_patient_success(self, api_client):
        """Patient registration should succeed with auto-approval."""
        url = reverse("register")
        data = {
            "email": "patient@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "role": "PATIENT",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert response.data["user"]["role"] == "PATIENT"
        assert response.data["user"]["is_approved"] is True
        assert "access" in response.data
        assert "refresh" in response.data

        # Verify PatientProfile was created
        user = User.objects.get(email="patient@test.com")
        assert hasattr(user, "patient_profile")

    def test_register_doctor_pending_approval(self, api_client):
        """Doctor registration should succeed but set is_approved=False."""
        url = reverse("register")
        data = {
            "email": "doctor@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "role": "DOCTOR",
            "first_name": "Sarah",
            "last_name": "Chen",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == "DOCTOR"
        assert response.data["user"]["is_approved"] is False

    def test_register_duplicate_email(self, api_client, patient_user):
        """Registration with existing email should return 400."""
        url = reverse("register")
        data = {
            "email": patient_user.email,
            "password": "testpass123",
            "password_confirm": "testpass123",
            "role": "PATIENT",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_password_mismatch(self, api_client):
        """Registration with mismatched passwords should return 400."""
        url = reverse("register")
        data = {
            "email": "patient@test.com",
            "password": "testpass123",
            "password_confirm": "differentpassword",
            "role": "PATIENT",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_register_admin_role_blocked(self, api_client):
        """Admin registration should be blocked."""
        url = reverse("register")
        data = {
            "email": "admin@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "role": "ADMIN",
            "first_name": "Admin",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "role" in response.data


# ==========================
# Login Tests
# ==========================

@pytest.mark.django_db
class TestLogin:
    """Tests for POST /api/token/."""

    def test_login_valid_credentials(self, api_client, patient_user):
        """Valid credentials should return tokens + user."""
        url = reverse("token_obtain_pair")
        data = {"email": "patient@test.com", "password": "testpass123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "patient@test.com"

    def test_login_invalid_password(self, api_client, patient_user):
        """Invalid password should return 401."""
        url = reverse("token_obtain_pair")
        data = {"email": "patient@test.com", "password": "wrongpassword"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_login_unapproved_doctor(self, api_client, unapproved_doctor):
        """Unapproved doctor should be blocked with 401."""
        url = reverse("token_obtain_pair")
        data = {"email": "pending@test.com", "password": "testpass123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, api_client):
        """Inactive user should be blocked."""
        user = User.objects.create_user(
            email="inactive@test.com",
            password="testpass123",
            first_name="Inactive",
            last_name="User",
            role="PATIENT",
            is_approved=True,
            is_active=False,
        )
        url = reverse("token_obtain_pair")
        data = {"email": "inactive@test.com", "password": "testpass123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        """Nonexistent user should return 401."""
        url = reverse("token_obtain_pair")
        data = {"email": "nonexistent@test.com", "password": "testpass123"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==========================
# Token Refresh Tests
# ==========================

@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for POST /api/token/refresh/."""

    def test_refresh_valid_token(self, api_client, patient_user):
        """Valid refresh token should return new access token."""
        refresh = RefreshToken.for_user(patient_user)
        url = reverse("token_refresh")
        data = {"refresh": str(refresh)}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client):
        """Invalid refresh token should return 401."""
        url = reverse("token_refresh")
        data = {"refresh": "invalid-token"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_refresh_no_token(self, api_client):
        """Missing refresh token should return 400."""
        url = reverse("token_refresh")
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==========================
# User Model Tests
# ==========================

@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""

    def test_user_str_representation(self, patient_user):
        """User string should include email and role."""
        assert str(patient_user) == "patient@test.com (PATIENT)"

    def test_user_email_is_username_field(self):
        """User should use email as the primary identifier."""
        from apps.users.models import User
        assert User.USERNAME_FIELD == "email"
