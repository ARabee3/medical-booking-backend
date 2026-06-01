# Database Architecture

**Status:** Backend implementation guide. Django models must match this schema exactly.

This document defines the PostgreSQL schema that Django will implement. It exists so that:
1. The mock data structure matches the real database
2. There is zero ambiguity when switching to Django
3. The team can review and agree on relationships before backend work starts

---

## 1. Entity Relationship Diagram

```
User (AbstractUser)
├── id (PK)
├── email (unique)
├── password (hashed)
├── first_name
├── last_name
├── role (ADMIN, DOCTOR, PATIENT)
├── is_active
├── is_approved
├── date_joined
├── last_login
│
├── 1:1 DoctorProfile
│   ├── id (PK)
│   ├── user_id (FK → User)
│   ├── specialty_id (FK → Specialty, nullable)
│   ├── bio (text)
│   ├── image_url
│   └── phone
│
├── 1:1 PatientProfile
│   ├── id (PK)
│   ├── user_id (FK → User)
│   ├── phone
│   ├── date_of_birth
│   └── emergency_contact_name
│   └── emergency_contact_phone
│
└── (Admin has no extra profile — uses User.role = ADMIN)

Specialty
├── id (PK)
├── name (unique)
├── description
└── icon (optional)

Availability
├── id (PK)
├── doctor_id (FK → DoctorProfile)
├── date (date)
├── start_time (time)
├── end_time (time)
├── is_booked (boolean, default false)
└── created_at

Appointment
├── id (PK)
├── patient_id (FK → User, where role = PATIENT)
├── doctor_id (FK → User, where role = DOCTOR)
├── availability_id (FK → Availability, nullable)
├── date (date)
├── time (time)
├── status (PENDING, CONFIRMED, COMPLETED, CANCELLED)
├── notes (text, nullable)
├── created_at
└── updated_at
```

---

## 2. Table Definitions

### users_user (Custom User — extends AbstractUser)

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| password | VARCHAR(128) | NOT NULL |
| last_login | TIMESTAMP | NULL |
| is_superuser | BOOLEAN | DEFAULT FALSE |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| first_name | VARCHAR(150) | NOT NULL |
| last_name | VARCHAR(150) | NOT NULL |
| is_staff | BOOLEAN | DEFAULT FALSE |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_approved | BOOLEAN | DEFAULT FALSE |
| date_joined | TIMESTAMP | DEFAULT NOW() |
| role | VARCHAR(10) | NOT NULL, CHECK (role IN ('ADMIN', 'DOCTOR', 'PATIENT')) |

**Indexes:**
- UNIQUE on email
- Index on role (for filtering)
- Index on is_active (for admin queries)

---

### doctors_doctorprofile

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| user_id | INTEGER | UNIQUE, FK → users_user(id), ON DELETE CASCADE |
| specialty_id | INTEGER | FK → specialties_specialty(id), ON DELETE SET NULL |
| bio | TEXT | NULL |
| image_url | VARCHAR(500) | NULL |
| phone | VARCHAR(20) | NULL |

**Rationale:** Separate profile keeps User table clean. CASCADE delete removes profile when user is deleted.

---

### patients_patientprofile

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| user_id | INTEGER | UNIQUE, FK → users_user(id), ON DELETE CASCADE |
| phone | VARCHAR(20) | NULL |
| date_of_birth | DATE | NULL |
| emergency_contact_name | VARCHAR(150) | NULL |
| emergency_contact_phone | VARCHAR(20) | NULL |

---

### specialties_specialty

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| description | TEXT | NULL |
| icon | VARCHAR(100) | NULL |

**Seed Data:**
- Cardiology
- Dermatology
- Neurology
- Pediatrics
- Orthopedics
- General Practice

---

### doctors_availability

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| doctor_id | INTEGER | FK → doctors_doctorprofile(id), ON DELETE CASCADE |
| date | DATE | NOT NULL |
| start_time | TIME | NOT NULL |
| end_time | TIME | NOT NULL |
| is_booked | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | DEFAULT NOW() |

**Constraints:**
- `CHECK (end_time > start_time)` — end must be after start
- `CHECK (date >= CURRENT_DATE)` — no past dates (optional, application-level better)

**Indexes:**
- Index on (doctor_id, date) — most common query
- Index on is_booked — for finding open slots

**Unique Constraint:**
- (doctor_id, date, start_time) — prevent overlapping at DB level (additional app validation needed)

---

### appointments_appointment

| Column | Type | Constraints |
|--------|------|------------|
| id | SERIAL | PRIMARY KEY |
| patient_id | INTEGER | FK → users_user(id), ON DELETE CASCADE |
| doctor_id | INTEGER | FK → users_user(id), ON DELETE CASCADE |
| availability_id | INTEGER | FK → doctors_availability(id), ON DELETE SET NULL |
| date | DATE | NOT NULL |
| time | TIME | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'PENDING', CHECK (status IN ('PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED')) |
| notes | TEXT | NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

**Indexes:**
- Index on patient_id (for "My Appointments")
- Index on doctor_id (for doctor dashboard)
- Index on status (for admin filtering)
- Index on date (for calendar queries)

**Constraints:**
- Patient's role must be PATIENT (application-level validation in serializer)
- Doctor's role must be DOCTOR (application-level validation in serializer)

---

## 3. Relationships Summary

```
User 1:1 DoctorProfile
User 1:1 PatientProfile
Specialty 1:N DoctorProfile
DoctorProfile 1:N Availability
User (Patient) 1:N Appointment
User (Doctor) 1:N Appointment
Availability 1:0..1 Appointment
```

---

## 4. Data Integrity Rules

1. **User Registration:**
   - New DOCTOR accounts have `is_approved = FALSE` until admin approves
   - New PATIENT accounts have `is_approved = TRUE` (auto-approved)
   - ADMIN accounts are created manually or via management command

2. **Appointment Booking:**
   - An availability slot with `is_booked = TRUE` cannot be booked again
   - Booking sets `availability.is_booked = TRUE`
   - Cancelling sets `availability.is_booked = FALSE` (if availability_id exists)

3. **Rescheduling:**
   - Old availability slot becomes available (`is_booked = FALSE`)
   - New availability slot becomes booked (`is_booked = TRUE`)
   - Or create new availability if no slot exists

4. **Doctor Status:**
   - If `user.is_active = FALSE`, doctor does not appear in patient search
   - If `user.is_approved = FALSE`, doctor cannot log in

---

## 5. Key Django Models (Reference)

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
    ]
    username = None  # Use email instead
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

# apps/doctors/models.py
class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    bio = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

class Availability(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='end_after_start'
            ),
        ]

# apps/appointments/models.py
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    availability = models.ForeignKey(Availability, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 6. Notes for Backend Implementation

- Mock data should mirror these shapes exactly
- The `id` fields should be sequential integers (1, 2, 3...)
- Dates are strings `YYYY-MM-DD` in JSON
- Times are strings `HH:mm` in JSON
- `created_at` is ISO 8601 string
- Boolean fields are JSON `true`/`false`
