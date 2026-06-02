"""
Users app views.

Authentication endpoints matching the frontend API contract:
- POST /api/register/
- POST /api/token/
- POST /api/token/refresh/
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/register/

    Creates a new user account:
    - PATIENT accounts are auto-approved
    - DOCTOR accounts require admin approval (is_approved=False)
    - Returns user object + JWT pair
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/token/

    Custom login endpoint that:
    - Validates email/password
    - Blocks inactive users
    - Blocks unapproved doctors
    - Returns access + refresh tokens + user object
    """

    serializer_class = CustomTokenObtainPairSerializer
