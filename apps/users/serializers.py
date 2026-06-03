"""
Users app serializers.

Handles registration and JWT authentication with custom user model.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from apps.doctors.models import DoctorProfile
from .models import PatientProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "is_active", "is_approved"]
        read_only_fields = ["id", "is_active", "is_approved"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "role", "first_name", "last_name"]

    def validate(self, attrs):
        """Validate password match and role restrictions."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password": ["Passwords do not match."]}
            )

        role = attrs.get("role")
        if role == "ADMIN":
            raise serializers.ValidationError(
                {"role": ["Admin accounts cannot be created via registration."]}
            )

        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": ["User with this email already exists."]}
            )

        return attrs

    def create(self, validated_data):
        """Create user with role-based approval logic."""
        role = validated_data["role"]
        is_approved = role == "PATIENT"  # Auto-approve patients, doctors need admin approval

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=role,
            is_approved=is_approved,
        )

        if role == "PATIENT":
            PatientProfile.objects.create(user=user)
        elif role == "DOCTOR":
            DoctorProfile.objects.create(user=user)

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that:
    - Checks is_active and is_approval status
    - Includes user object in response (matches frontend mock API)
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if not user.is_active:
            raise AuthenticationFailed(
                "No active account found with the given credentials"
            )

        if not user.is_approved:
            raise AuthenticationFailed(
                "No active account found with the given credentials"
            )

        data["user"] = UserSerializer(user).data
        return data
