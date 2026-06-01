# Third-party packages
import django_filters

# Django
from django.contrib.auth import get_user_model
from django.db.models import Q

# Local / project imports
from apps.appointments.models import Appointment

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Filter set for admin user list endpoint.

    Supports:
        role        -- exact match (ADMIN, DOCTOR, PATIENT)
        is_active   -- boolean
        is_approved -- boolean
        search      -- case-insensitive match on first_name, last_name, or email
    """

    search = django_filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = User
        fields = {
            "role": ["exact"],
            "is_active": ["exact"],
            "is_approved": ["exact"],
        }

    def filter_search(self, queryset, name, value):
        """Search across first_name, last_name, and email (case-insensitive)."""
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )


class AppointmentFilter(django_filters.FilterSet):
    """Filter set for admin appointment overview endpoint.

    Supports:
        status    -- exact match on appointment status
        date_from -- appointments on or after this date (inclusive)
        date_to   -- appointments on or before this date (inclusive)
    """

    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to   = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Appointment
        fields = {
            "status": ["exact"],
        }