# Backend Coding Conventions & Standards

**Applies to:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Enforced by:** Team agreement + pre-commit hooks (future)

---

## 1. File & Folder Naming

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `models.py`, `serializers.py`, `test_views.py` |
| Django apps | snake_case | `apps/users/`, `apps/doctors/` |
| Classes | PascalCase | `UserSerializer`, `DoctorProfileView` |
| Functions/Methods | snake_case | `get_queryset()`, `validate_email()` |
| Constants | UPPER_SNAKE_CASE | `ROLE_CHOICES`, `STATUS_PENDING` |
| Test files | `test_*.py` or `*_tests.py` | `test_models.py`, `auth_tests.py` |
| Fixtures | snake_case | `conftest.py`, `demo_users.json` |

---

## 2. Import Ordering (isort style)

Follow this order with a blank line between groups:

```python
# 1. Standard library
import os
from datetime import timedelta

# 2. Third-party packages
from rest_framework import serializers, status
from rest_framework.response import Response

# 3. Django
from django.db import models
from django.contrib.auth import get_user_model

# 4. Local / project imports
from apps.doctors.models import DoctorProfile
from shared.permissions import IsDoctor
```

**Rule:** Use absolute imports within the project. Never use relative imports (`from .models import ...`) except within the same app for models.

---

## 3. Model Pattern

Every model must include:
- `Meta` class with `db_table` name
- `__str__` method
- `verbose_name` / `verbose_name_plural` where applicable
- Docstring explaining purpose

```python
from django.db import models


class Specialty(models.Model):
    """Medical specialty (e.g., Cardiology, Dermatology)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "specialties_specialty"
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name
```

---

## 4. Serializer Pattern (DRF)

- Use `ModelSerializer` when possible
- Explicitly list `fields` (never use `"__all__"`)
- Add `read_only_fields` where appropriate
- Validate in `validate()` or field-specific methods

```python
from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "is_active", "is_approved"]
        read_only_fields = ["id", "is_active", "is_approved"]
```

---

## 5. View Pattern (DRF)

Prefer class-based views (`APIView`, ` generics.*APIView`, `ViewSet`):

```python
from rest_framework import generics, permissions
from shared.permissions import IsPatient
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListView(generics.ListCreateAPIView):
    """List and create appointments for the current patient."""

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user)
```

---

## 6. URL Pattern

Keep URLConfs flat and readable. Use `path()` with named routes:

```python
from django.urls import path
from .views import DoctorListView, DoctorDetailView

urlpatterns = [
    path("doctors/", DoctorListView.as_view(), name="doctor-list"),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
]
```

---

## 7. Test Pattern (pytest-django)

Use fixtures from `conftest.py`. Name tests descriptively:

```python
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAppointmentBooking:
    """Tests for patient appointment booking endpoint."""

    def test_patient_can_book_appointment(self, api_client, patient_user, doctor_user, availability):
        url = reverse("appointment-list")
        data = {
            "doctor_id": doctor_user.id,
            "date": "2026-01-20",
            "time": "09:00",
        }
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert response.data["status"] == "PENDING"

    def test_double_booking_returns_400(self, api_client, patient_user, booked_appointment):
        # ...
        pass
```

**Test naming:** `test_<subject>_<action>_<expected_result>`

---

## 8. Docstring Rules

Use Google-style docstrings for functions/classes:

```python
def filter_by_role(queryset, user):
    """Filter a queryset based on the user's role.

    Args:
        queryset: The base queryset to filter.
        user: The authenticated user instance.

    Returns:
        QuerySet: The filtered queryset.
    """
    # ...
```

---

## 9. Error Handling

Raise `ValidationError` in serializers for business logic errors.
Use DRF's built-in permission classes for access control.

```python
from rest_framework.exceptions import ValidationError


def validate_no_double_booking(attrs):
    doctor_id = attrs.get("doctor_id")
    date = attrs.get("date")
    time = attrs.get("time")

    if Appointment.objects.filter(
        doctor_id=doctor_id, date=date, time=time
    ).exists():
        raise ValidationError({"time": "This time slot is no longer available."})
```

---

## 10. Environment Variables

All configurable values must come from environment variables via `.env`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

Never hardcode secrets, database credentials, or debug flags.

---

## 11. Linting & Formatting

**Black:** Code formatter. Line length 88.  
**isort:** Import sorter.  
**flake8:** Linter. Max line length 88 (match Black).  
**pytest:** Test runner.

```bash
make format   # Run Black
make lint     # Run flake8
make test     # Run pytest
```

---

## 12. Comment Rules

```python
# Good: Why, not what
# Retry on 401 because token might have expired

# Bad: Obvious
# Set loading to true
is_loading = True
```

For complex logic, use docstrings (see section 8).
