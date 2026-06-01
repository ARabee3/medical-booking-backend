"""
Users app URL configuration.

Authentication endpoints matching the frontend API contract:
- POST /api/register/
- POST /api/token/
- POST /api/token/refresh/
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# TODO: Import custom views once implemented
# from .views import RegisterView

urlpatterns = [
    # path("register/", RegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
