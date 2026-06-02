# Django
from django.urls import path

# Local / project imports
from apps.admin_api.views import (
    AdminAppointmentListView,
    AdminSpecialtyDetailView,
    AdminSpecialtyListCreateView,
    AdminStatsView,
    AdminUserListView,
    AdminUserUpdateView,
)

urlpatterns = [
    # BE-016 — User management
    path("admin/users/",              AdminUserListView.as_view(),          name="admin-user-list"),
    path("admin/users/<int:pk>/",     AdminUserUpdateView.as_view(),        name="admin-user-update"),

    # BE-017 — Appointments overview
    path("admin/appointments/",       AdminAppointmentListView.as_view(),   name="admin-appointment-list"),

    # BE-018 — Dashboard stats
    path("admin/stats/",              AdminStatsView.as_view(),             name="admin-stats"),

    # Specialty CRUD
    path("admin/specialties/",        AdminSpecialtyListCreateView.as_view(), name="admin-specialty-list"),
    path("admin/specialties/<int:pk>/", AdminSpecialtyDetailView.as_view(), name="admin-specialty-detail"),
]