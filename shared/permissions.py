"""
Shared permission classes for role-based access control.

These mirror the frontend role guards (PrivateRoute.tsx) on the backend.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allow access only to users with role=ADMIN."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsDoctor(permissions.BasePermission):
    """Allow access only to users with role=DOCTOR."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "DOCTOR"
        )


class IsPatient(permissions.BasePermission):
    """Allow access only to users with role=PATIENT."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PATIENT"
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: allow if user is the owner of the object
    or has ADMIN role. Assumes the object has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True
        return obj.user == request.user


class ReadOnly(permissions.BasePermission):
    """Allow only safe methods (GET, HEAD, OPTIONS)."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
