# Backend User Stories

**Team:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Phase:** Django Backend  
**Mapping:** Each BE story corresponds to frontend US stories and API contract endpoints.

---

## Epic: Backend Infrastructure (Ahmed)

### BE-Phase 0: Django Project Scaffold
**As a** team, **I want** a solid Django project foundation, **so that** we can all build features in parallel without conflicts.

**Acceptance Criteria:**
- [ ] `config/settings/base.py` with DRF, SimpleJWT, CORS, custom User model reference
- [ ] `config/settings/local.py` with DEBUG=True, PostgreSQL config from env
- [ ] `config/settings/production.py` with security headers, whitenoise
- [ ] `manage.py` works and can run migrations
- [ ] `Makefile` with `run`, `test`, `migrate`, `lint` commands
- [ ] `pytest.ini` configured with `DJANGO_SETTINGS_MODULE=config.settings.local`
- [ ] `.env.example` with all required variables documented

**Related Files:**
- `config/settings/base.py`, `local.py`, `production.py`
- `Makefile`, `pytest.ini`, `.env.example`

**Points:** 3 | **Owner:** Ahmed | **Epic:** Backend Infrastructure

---

### BE-001: Custom User Model
**As a** developer, **I want** a custom User model with email-based login and roles, **so that** the backend matches the frontend auth contract.

**Acceptance Criteria:**
- [ ] Extend `AbstractUser`, remove `username` field
- [ ] `email` field is `UNIQUE` and used as `USERNAME_FIELD`
- [ ] `role` choices: `ADMIN`, `DOCTOR`, `PATIENT`
- [ ] `is_approved` BooleanField (default `False` for doctors, `True` for patients)
- [ ] `first_name` and `last_name` are required
- [ ] Create `PatientProfile` 1:1 linked model with `phone`, `date_of_birth`, `emergency_contact_name`, `emergency_contact_phone`
- [ ] Admin can view/manage users via Django admin
- [ ] `AUTH_USER_MODEL = "users.User"` in `config/settings/base.py`

**Related Files:**
- `apps/users/models.py`
- `apps/users/admin.py`
- `config/settings/base.py`

**API Contract Reference:** Registration returns:
```json
{
  "user": { "id", "email", "first_name", "last_name", "role", "is_active" },
  "access": "...",
  "refresh": "..."
}
```

**Points:** 3 | **Owner:** Ahmed | **Epic:** Auth & Routing

---

### BE-002: JWT Authentication Endpoints
**As a** user, **I want** to register, log in, and refresh my token, **so that** I can authenticate with the backend.

**Acceptance Criteria:**
- [ ] `POST /api/register/` — creates User + PatientProfile, returns user + JWT pair
- [ ] `POST /api/token/` — returns access + refresh tokens (DRF SimpleJWT)
- [ ] `POST /api/token/refresh/` — returns new access token (DRF SimpleJWT)
- [ ] Registration validates: unique email, password match, role required
- [ ] Patient accounts are auto-approved (`is_approved=True`)
- [ ] Doctor accounts are pending approval (`is_approved=False`)
- [ ] Login fails with 401 for unapproved doctors

**Related Files:**
- `apps/users/views.py`
- `apps/users/serializers.py`
- `apps/users/urls.py`

**API Contract Reference:** See `docs/API_CONTRACT.md` — Authentication section

**Points:** 3 | **Owner:** Ahmed | **Epic:** Auth & Routing

---

### BE-003: Shared Utilities
**As a** developer, **I want** reusable permissions, pagination, and error formatting, **so that** all endpoints behave consistently.

**Acceptance Criteria:**
- [ ] `IsAdmin`, `IsDoctor`, `IsPatient` permission classes
- [ ] `IsOwnerOrAdmin` object-level permission
- [ ] `StandardResultsSetPagination` with page_size=20
- [ ] `RoleFilteredQuerysetMixin` for patient/doctor-scoped queries
- [ ] `custom_exception_handler` matching frontend `ApiError` shape: `{"detail": "..."}` or `{"field": ["error"]}`

**Related Files:**
- `shared/permissions.py`
- `shared/pagination.py`
- `shared/mixins.py`
- `shared/exceptions.py`

**Points:** 2 | **Owner:** Ahmed | **Epic:** Backend Infrastructure

---

### BE-004: PostgreSQL Setup
**As a** developer, **I want** the backend to connect to PostgreSQL via environment variables, **so that** we use the same DB in dev and production.

**Acceptance Criteria:**
- [ ] `DATABASES` in `base.py` reads from env vars: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- [ ] `python-dotenv` loads `.env` file at startup
- [ ] Team can run `createdb medical_booking` and `make migrate` successfully
- [ ] `.env.example` documents all DB variables

**Related Files:**
- `config/settings/base.py`
- `.env.example`

**Points:** 2 | **Owner:** Ahmed | **Epic:** Backend Infrastructure

---

### BE-005: Pytest Configuration
**As a** team, **I want** a test suite with fixtures, **so that** we can verify features before merging.

**Acceptance Criteria:**
- [ ] `pytest.ini` configured with `DJANGO_SETTINGS_MODULE=config.settings.local`
- [ ] `conftest.py` with fixtures: `api_client`, `patient_user`, `doctor_user`, `admin_user`, `specialty`, `availability`
- [ ] First auth tests pass: register, login, token refresh
- [ ] `make pytest` runs all tests

**Related Files:**
- `pytest.ini`
- `conftest.py` (to be created at repo root or `apps/`)

**Points:** 2 | **Owner:** Ahmed | **Epic:** Backend Infrastructure

---

## Epic: Doctors (Abdulazim)

### BE-006: Specialty & DoctorProfile Models
**As a** developer, **I want** doctor-related models, **so that** patients can browse and book with real doctors.

**Acceptance Criteria:**
- [ ] `Specialty` model with `name` (unique), `description`, `icon`
- [ ] `DoctorProfile` model with 1:1 `User`, FK `Specialty`, `bio`, `image_url`, `phone`
- [ ] `Availability` model with FK `DoctorProfile`, `date`, `start_time`, `end_time`, `is_booked`
- [ ] DB constraint: `end_time > start_time`
- [ ] Seed script for 6 specialties: Cardiology, Dermatology, Neurology, Pediatrics, Orthopedics, General Practice
- [ ] Admin configuration for all 3 models

**Related Files:**
- `apps/doctors/models.py`
- `apps/doctors/admin.py`
- `scripts/seed_specialties.py`

**Points:** 3 | **Owner:** Abdulazim | **Epic:** Doctors

---

### BE-007: GET /api/doctors/
**As a** patient, **I want** to see all approved doctors with filtering, **so that** I can find the right specialist.

**Acceptance Criteria:**
- [ ] `GET /api/doctors/` returns list of approved, active doctors
- [ ] Query param `specialty` filters by specialty name
- [ ] Query param `search` searches by doctor name (first_name + last_name)
- [ ] Only doctors with `is_active=True` and `is_approved=True` are returned
- [ ] Response shape matches `docs/API_CONTRACT.md` exactly
- [ ] Uses `StandardResultsSetPagination`

**Related Files:**
- `apps/doctors/views.py`
- `apps/doctors/serializers.py`
- `apps/doctors/urls.py`

**API Contract Reference:**
```json
[
  {
    "id": 1,
    "user_id": 2,
    "name": "Dr. Sarah Chen",
    "email": "sarah.chen@hospital.com",
    "specialty": "Cardiology",
    "bio": "...",
    "image_url": "...",
    "is_active": true
  }
]
```

**Points:** 2 | **Owner:** Abdulazim | **Epic:** Doctors

---

### BE-008: GET /api/doctors/:id/
**As a** patient, **I want** to view a doctor's full profile, **so that** I can decide whether to book.

**Acceptance Criteria:**
- [ ] `GET /api/doctors/<id>/` returns full doctor profile
- [ ] 404 if doctor not found or not active/approved
- [ ] Response shape matches API contract exactly

**Related Files:**
- `apps/doctors/views.py`
- `apps/doctors/serializers.py`

**Points:** 2 | **Owner:** Abdulazim | **Epic:** Doctors

---

### BE-009: GET /api/doctors/:id/availability/
**As a** patient, **I want** to see a doctor's available slots for a date, **so that** I can choose a time.

**Acceptance Criteria:**
- [ ] `GET /api/doctors/<id>/availability/?date=YYYY-MM-DD`
- [ ] Returns only slots where `is_booked=False` and `date >= today`
- [ ] Response shape: `{ "doctor_id": 1, "date": "...", "slots": ["09:00", ...] }`
- [ ] Returns empty `slots` array if no availability
- [ ] 404 if doctor not found

**Related Files:**
- `apps/doctors/views.py`
- `apps/doctors/serializers.py`

**Points:** 3 | **Owner:** Abdulazim | **Epic:** Doctors

---

## Epic: Appointments (Gerges)

### BE-010: Appointment Model
**As a** developer, **I want** an Appointment model, **so that** patients can book and doctors can manage.

**Acceptance Criteria:**
- [ ] `Appointment` model with FK `patient` (User), FK `doctor` (User), FK `availability` (nullable)
- [ ] Fields: `date`, `time`, `status` (PENDING/CONFIRMED/COMPLETED/CANCELLED), `notes`, `created_at`, `updated_at`
- [ ] Indexes on `patient_id`, `doctor_id`, `status`, `date`
- [ ] Admin configuration with list_display and filters

**Related Files:**
- `apps/appointments/models.py`
- `apps/appointments/admin.py`

**Points:** 2 | **Owner:** Gerges | **Epic:** Appointments

---

### BE-011: Patient Booking — POST /api/appointments/
**As a** patient, **I want** to book an appointment, **so that** I can see a doctor.

**Acceptance Criteria:**
- [ ] `POST /api/appointments/` with `doctor_id`, `date`, `time`
- [ ] Validates slot is available (`is_booked=False`)
- [ ] Validates date is not in the past
- [ ] Sets `availability.is_booked = True`
- [ ] Returns appointment with `status: "PENDING"`
- [ ] 400 with field errors if validation fails
- [ ] 403 if user is not a patient

**Related Files:**
- `apps/appointments/views.py`
- `apps/appointments/serializers.py`
- `apps/appointments/services.py`

**API Contract Reference:** See `docs/API_CONTRACT.md` — Appointments section

**Points:** 3 | **Owner:** Gerges | **Epic:** Appointments

---

### BE-012: Appointment Modifications — PATCH cancel & reschedule
**As a** patient, **I want** to cancel or reschedule my appointment, **so that** I can manage my bookings.

**Acceptance Criteria:**
- [ ] `PATCH /api/appointments/<id>/` with `status: "CANCELLED"` → cancels appointment
- [ ] `PATCH /api/appointments/<id>/` with `date` and `time` → reschedules
- [ ] Cancelling sets `availability.is_booked = False` (if linked)
- [ ] Rescheduling validates new slot is available, releases old slot
- [ ] Only the owning patient can modify (403 otherwise)
- [ ] Returns updated appointment object

**Related Files:**
- `apps/appointments/views.py`
- `apps/appointments/services.py`

**Points:** 3 | **Owner:** Gerges | **Epic:** Appointments

---

### BE-013: Doctor Dashboard — GET /api/doctor/appointments/
**As a** doctor, **I want** to see my appointments, **so that** I can manage my schedule.

**Acceptance Criteria:**
- [ ] `GET /api/doctor/appointments/` returns appointments where `doctor=request.user`
- [ ] Patient info included in response (name, email)
- [ ] 403 if user is not a doctor

**Related Files:**
- `apps/appointments/views.py`

**API Contract Reference:**
```json
[
  {
    "id": 1,
    "patient": { "id": 3, "name": "John Doe", "email": "patient@example.com" },
    "date": "2026-01-20",
    "time": "09:00",
    "status": "PENDING",
    "notes": null,
    "created_at": "..."
  }
]
```

**Points:** 2 | **Owner:** Gerges | **Epic:** Appointments

---

### BE-014: Doctor Actions — Approve/reject appointments
**As a** doctor, **I want** to approve or reject appointment requests, **so that** patients know if I can see them.

**Acceptance Criteria:**
- [ ] `PATCH /api/doctor/appointments/<id>/` with `status: "CONFIRMED"` or `"CANCELLED"`
- [ ] Doctor can add optional `notes`
- [ ] Validates the appointment belongs to this doctor (403 otherwise)
- [ ] Returns updated appointment

**Related Files:**
- `apps/appointments/views.py`
- `apps/appointments/serializers.py`

**Points:** 2 | **Owner:** Gerges | **Epic:** Appointments

---

## Epic: Admin (Mokhtar)

### BE-015: Doctor Availability Management
**As a** doctor, **I want** to add and remove my availability slots, **so that** patients can book with me.

**Acceptance Criteria:**
- [ ] `POST /api/doctor/availability/` with `date`, `start_time`, `end_time`
- [ ] Validates no overlapping slots for this doctor
- [ ] Validates date is not in the past
- [ ] `DELETE /api/doctor/availability/<id>/` removes slot
- [ ] Cannot delete a slot that is already booked (400)
- [ ] 403 if user is not the owner doctor

**Related Files:**
- `apps/appointments/views.py`
- `apps/appointments/serializers.py`

**Points:** 3 | **Owner:** Mokhtar | **Epic:** Admin

---

### BE-016: Admin User Table
**As an** admin, **I want** to manage all users, **so that** I can approve doctors and block accounts.

**Acceptance Criteria:**
- [ ] `GET /api/admin/users/` returns all users with pagination
- [ ] Query params: `role`, `is_active`, `is_approved`, `search` (name/email)
- [ ] `PATCH /api/admin/users/<id>/` updates `is_active`, `is_approved`
- [ ] 403 if user is not admin
- [ ] Response shape matches API contract exactly

**Related Files:**
- `apps/admin_api/views.py`
- `apps/admin_api/serializers.py`
- `apps/admin_api/filters.py`

**Points:** 3 | **Owner:** Mokhtar | **Epic:** Admin

---

### BE-017: Admin Appointments Overview
**As an** admin, **I want** to see all system appointments, **so that** I can monitor activity.

**Acceptance Criteria:**
- [ ] `GET /api/admin/appointments/` returns all appointments
- [ ] Query params: `status`, `date_from`, `date_to`
- [ ] Full doctor and patient objects included
- [ ] Sortable by date, status
- [ ] 403 if user is not admin

**Related Files:**
- `apps/admin_api/views.py`
- `apps/admin_api/filters.py`

**Points:** 2 | **Owner:** Mokhtar | **Epic:** Admin

---

### BE-018: Admin Stats
**As an** admin, **I want** system statistics, **so that** I can see activity at a glance.

**Acceptance Criteria:**
- [ ] `GET /api/admin/stats/` returns:
  - `total_users`
  - `total_doctors`
  - `total_appointments`
  - `pending_approvals`
- [ ] 403 if user is not admin

**Related Files:**
- `apps/admin_api/views.py`

**Points:** 2 | **Owner:** Mokhtar | **Epic:** Admin

---

## Epic: Polish & Integration (Team)

### BE-019: Comprehensive API Tests
**As a** team, **I want** tests covering all endpoints and permissions, **so that** we catch regressions early.

**Acceptance Criteria:**
- [ ] Tests for all auth endpoints (register, login, refresh)
- [ ] Tests for doctor listing and filtering
- [ ] Tests for booking, cancelling, rescheduling
- [ ] Tests for doctor approve/reject
- [ ] Tests for admin endpoints
- [ ] Permission tests: patient can't access doctor endpoints, doctor can't access admin endpoints
- [ ] Edge case tests: double booking, past date booking, deleting booked slot

**Points:** 3 | **Owner:** Ahmed (coordinated) | **Epic:** Backend Infrastructure

---

### BE-020: Demo Data Seeding
**As a** team, **I want** realistic demo data, **so that** we can test the frontend integration.

**Acceptance Criteria:**
- [ ] Management command: `python manage.py seed_demo_data`
- [ ] Creates: 6 specialties, 10 doctors, 20 patients, 50+ availability slots, 10+ appointments
- [ ] Data mirrors frontend mock data structure
- [ ] Doctors have realistic bios, specialties, and availability

**Points:** 2 | **Owner:** Mokhtar | **Epic:** Backend Infrastructure

---

### BE-021: Frontend Integration
**As a** team, **I want** the React frontend to connect to Django, **so that** we have a working full-stack app.

**Acceptance Criteria:**
- [ ] `django-cors-headers` configured to allow `localhost:5173`
- [ ] Frontend `.env` updated to `VITE_API_BASE_URL=http://localhost:8000/api`
- [ ] All frontend mock API calls replaced with real Axios calls
- [ ] JWT interceptor works with Django tokens
- [ ] End-to-end smoke test: register → login → browse doctors → book appointment

**Points:** 3 | **Owner:** Ahmed | **Epic:** Backend Infrastructure

---

## Story Summary by Owner

| Owner | Stories | Total Points |
|-------|---------|-------------|
| Ahmed | BE-Phase 0, BE-001 to BE-005, BE-019, BE-021 | 18 |
| Abdulazim | BE-006 to BE-009 | 10 |
| Gerges | BE-010 to BE-014 | 12 |
| Mokhtar | BE-015 to BE-018, BE-020 | 10 |
| **Total** | **22 stories** | **50 points** |

---

## Definition of Done (All Stories)

- [ ] Feature implemented against API contract (`docs/API_CONTRACT.md`)
- [ ] All tests pass (`make pytest`)
- [ ] No flake8 or Black warnings (`make lint`, `make format-check`)
- [ ] Follows conventions in `docs/BACKEND_CONVENTIONS.md`
- [ ] PR reviewed and approved by at least 1 teammate
- [ ] Branch merged into `develop`
