"""
Doctors app URL configuration.

Endpoints:
- GET /api/doctors/
- GET /api/doctors/:id/
- GET /api/doctors/:id/availability/
- GET /api/doctors/:id/availability/summary/
- GET /api/doctors/:id/images/
- PATCH /api/doctors/me/update/
- POST /api/doctors/me/avatar/
- DELETE /api/doctors/me/avatar/
- GET, POST /api/doctors/me/images/
- GET, PATCH, DELETE /api/doctors/me/images/:id/
- GET /api/doctors/:id/reviews/
- GET /api/doctors/me/reviews/
"""

from django.urls import path

from .views import (
    AvailabilityListView,
    AvailabilitySummaryView,
    CurrentDoctorView,
    CurrentDoctorUpdateView,
    CurrentDoctorReviewsView,
    AvatarUploadView,
    AvatarDeleteView,
    DoctorDetailView,
    DoctorListView,
    DoctorImageListView,
    DoctorImageDetailView,
    PublicDoctorImagesView,
    DoctorReviewsView,
)

urlpatterns = [
    path("doctors/", DoctorListView.as_view(), name="doctor-list"),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    path("doctors/me/", CurrentDoctorView.as_view(), name="current-doctor"),
    path("doctors/me/update/", CurrentDoctorUpdateView.as_view(), name="current-doctor-update"),
    path("doctors/me/avatar/", AvatarUploadView.as_view(), name="doctor-avatar"),
    path("doctors/me/avatar/delete/", AvatarDeleteView.as_view(), name="doctor-avatar-delete"),
    path("doctors/me/images/", DoctorImageListView.as_view(), name="doctor-image-list"),
    path("doctors/me/images/<int:pk>/", DoctorImageDetailView.as_view(), name="doctor-image-detail"),
    path("doctors/<int:pk>/images/", PublicDoctorImagesView.as_view(), name="doctor-images-public"),
    path("doctors/<int:pk>/reviews/", DoctorReviewsView.as_view(), name="doctor-reviews"),
    path("doctors/me/reviews/", CurrentDoctorReviewsView.as_view(), name="current-doctor-reviews"),
    path(
        "doctors/<int:pk>/availability/",
        AvailabilityListView.as_view(),
        name="doctor-availability",
    ),
    path(
        "doctors/<int:pk>/availability/summary/",
        AvailabilitySummaryView.as_view(),
        name="doctor-availability-summary",
    ),
]
