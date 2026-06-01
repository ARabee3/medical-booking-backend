# Testing Strategy

**Applies to:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Framework:** pytest-django  
**Goal:** Every endpoint and permission must have test coverage.

---

## 1. Test Structure

Tests live in each app's folder or in a dedicated `tests/` directory:

```
apps/users/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   └── test_views.py
```

Or single `tests.py` for simple apps.

---

## 2. Fixtures

Create `conftest.py` at the project root or in `apps/`:

```python
import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.doctors.models import Specialty, DoctorProfile, Availability
from apps.appointments.models import Appointment


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def patient_user(db):
    """Create and return a patient user."""
    user = User.objects.create_user(
        email="patient@example.com",
        password="testpass123",
        first_name="John",
        last_name="Doe",
        role="PATIENT",
        is_approved=True,
    )
    return user


@pytest.fixture
def doctor_user(db):
    """Create and return a doctor user with profile."""
    user = User.objects.create_user(
        email="doctor@example.com",
        password="testpass123",
        first_name="Sarah",
        last_name="Chen",
        role="DOCTOR",
        is_approved=True,
    )
    specialty = Specialty.objects.create(name="Cardiology")
    DoctorProfile.objects.create(user=user, specialty=specialty, bio="Experienced cardiologist")
    return user


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_user(
        email="admin@example.com",
        password="testpass123",
        first_name="Admin",
        last_name="User",
        role="ADMIN",
        is_approved=True,
    )


@pytest.fixture
def specialty(db):
    """Create and return a specialty."""
    return Specialty.objects.create(name="Cardiology", description="Heart specialists")


@pytest.fixture
def availability(db, doctor_user):
    """Create and return an availability slot for the doctor."""
    profile = doctor_user.doctor_profile
    return Availability.objects.create(
        doctor=profile,
        date="2026-01-20",
        start_time="09:00",
        end_time="10:00",
        is_booked=False,
    )


@pytest.fixture
def booked_appointment(db, patient_user, doctor_user, availability):
    """Create and return a booked appointment."""
    availability.is_booked = True
    availability.save()
    return Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        availability=availability,
        date="2026-01-20",
        time="09:00",
        status="CONFIRMED",
    )
```

---

## 3. View Test Pattern

```python
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDoctorListEndpoint:
    """Tests for GET /api/doctors/."""

    def test_anonymous_user_can_list_doctors(self, api_client, doctor_user):
        url = reverse("doctor-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_filter_by_specialty(self, api_client, doctor_user):
        url = reverse("doctor-list")
        response = api_client.get(url, {"specialty": "Cardiology"})

        assert response.status_code == 200
        for doctor in response.data["results"]:
            assert doctor["specialty"] == "Cardiology"
```

---

## 4. Permission Test Pattern

```python
@pytest.mark.django_db
class TestAppointmentPermissions:
    """Tests that role-based permissions work correctly."""

    def test_patient_can_book_appointment(self, api_client, patient_user, doctor_user, availability):
        api_client.force_authenticate(user=patient_user)
        url = reverse("appointment-list")
        data = {
            "doctor_id": doctor_user.id,
            "date": "2026-01-20",
            "time": "09:00",
        }
        response = api_client.post(url, data)
        assert response.status_code == 201

    def test_doctor_cannot_book_appointment(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        url = reverse("appointment-list")
        response = api_client.post(url, {})
        assert response.status_code == 403

    def test_anonymous_cannot_access_appointments(self, api_client):
        url = reverse("appointment-list")
        response = api_client.get(url)
        assert response.status_code == 401
```

---

## 5. Serializer Test Pattern

```python
@pytest.mark.django_db
class TestUserSerializer:
    def test_user_serializer_output(self, patient_user):
        from apps.users.serializers import UserSerializer
        serializer = UserSerializer(patient_user)
        data = serializer.data

        assert data["email"] == "patient@example.com"
        assert data["role"] == "PATIENT"
        assert "password" not in data
```

---

## 6. Model Test Pattern

```python
@pytest.mark.django_db
class TestAppointmentModel:
    def test_default_status_is_pending(self, patient_user, doctor_user):
        appt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_user,
            date="2026-01-20",
            time="09:00",
        )
        assert appt.status == "PENDING"
```

---

## 7. Edge Case Tests

| Scenario | Test |
|----------|------|
| Double booking | Post same slot twice → second returns 400 |
| Past date booking | Post date in past → returns 400 |
| Unapproved doctor login | Login with `is_approved=False` → returns 401 |
| Deleting booked slot | Doctor tries DELETE on booked availability → returns 400 |
| Patient accessing doctor endpoint | Patient hits `/api/doctor/appointments/` → returns 403 |
| Admin accessing patient endpoint | Admin can access all → returns 200 |

---

## 8. Running Tests

```bash
# Run all tests
pytest

# Run specific app
pytest apps/users/tests/

# Run specific test file
pytest apps/users/tests/test_views.py

# Run with verbose output
pytest -v

# Run with coverage (install pytest-cov)
pytest --cov=apps --cov-report=html
```

---

## 9. CI/CD Testing (Future)

When CI is added (GitHub Actions):
- Run `pytest` on every PR
- Require 80%+ coverage for `main` branch
- Block merge if tests fail
