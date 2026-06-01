# Third-party packages
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

# Django
from django.contrib.auth import get_user_model

# Local / project imports
from shared.permissions import IsAdmin
from apps.admin_api.filters import UserFilter
from apps.admin_api.serializers import AdminUserSerializer

User = get_user_model()


class AdminUserListView(generics.ListAPIView):
    """List all users in the system with optional filtering and search.

    GET /api/admin/users/
    Accessible only by users with the ADMIN role.
    Supports filter params: role, is_active, is_approved, search.
    """

    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_queryset(self):
        return User.objects.all().order_by("id")


class AdminUserUpdateView(generics.UpdateAPIView):
    """Update a user's is_active or is_approved status.

    PATCH /api/admin/users/<id>/
    Accessible only by users with the ADMIN role.
    Only is_active and is_approved are writable (enforced by serializer).
    """

    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    http_method_names = ["patch"]  # Disable PUT — PATCH only per API contract

    def get_queryset(self):
        return User.objects.all()