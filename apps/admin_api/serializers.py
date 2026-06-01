# Third-party packages
from rest_framework import serializers

# Django
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management.

    Read fields: all user info.
    Writable fields: is_active, is_approved only.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_approved",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
        ]