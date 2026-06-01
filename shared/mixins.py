"""
Shared view mixins.

Provides reusable queryset filtering by role.
"""

class RoleFilteredQuerysetMixin:
    """
    Mixin that filters querysets based on the authenticated user's role.

    Usage:
        class MyView(generics.ListAPIView, RoleFilteredQuerysetMixin):
            def get_queryset(self):
                qs = super().get_queryset()
                return self.filter_by_role(qs)
    """

    def filter_by_role(self, queryset):
        user = self.request.user
        if user.role == "PATIENT":
            return queryset.filter(patient=user)
        if user.role == "DOCTOR":
            return queryset.filter(doctor=user)
        if user.role == "ADMIN":
            return queryset
        return queryset.none()
