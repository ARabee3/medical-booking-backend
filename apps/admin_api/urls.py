"""
Admin API URL configuration.

Endpoints:
- GET /api/admin/users/
- PATCH /api/admin/users/:id/
- GET /api/admin/appointments/
- GET /api/admin/stats/
"""

from django.urls import path

# TODO: Import views once implemented

urlpatterns = [
    # path("admin/users/", ...),
    # path("admin/appointments/", ...),
    # path("admin/stats/", ...),
]

# Django
from django.urls import path

# Local / project imports
from apps.admin_api.views import AdminUserListView, AdminUserUpdateView

urlpatterns = [
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:pk>/", AdminUserUpdateView.as_view(), name="admin-user-update"),
]