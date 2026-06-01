# Backend Project Structure

**Applies to:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Created by:** Ahmed (Phase 0 scaffold)  
**Maintained by:** Entire team with shared file rules

---

## 1. Top-Level Tree

```
medical-booking-backend/
├── docs/                           # Planning documents
│   ├── API_CONTRACT.md             # Copied from frontend — backend must match
│   ├── DATABASE_ARCHITECTURE.md    # Copied from frontend — Django models reference
│   ├── GIT_WORKFLOW.md             # Adapted from frontend
│   ├── BACKEND_CONVENTIONS.md      # Python/Django coding standards
│   ├── BACKEND_PROJECT_STRUCTURE.md # This file
│   ├── BACKEND_USER_STORIES.md    # Maps BE-00X to implementation tasks
│   ├── BACKEND_SETUP.md            # Onboarding guide
│   ├── TESTING_STRATEGY.md         # Pytest patterns & fixtures
│   └── DEPLOYMENT_NOTES.md        # Future deployment checklist
├── apps/                           # Domain-driven Django apps
│   ├── __init__.py
│   ├── users/                      # Ahmed
│   ├── doctors/                    # Abdulazim
│   ├── appointments/               # Gerges
│   └── admin_api/                  # Mokhtar (name avoids django.contrib.admin conflict)
├── shared/                         # Cross-cutting utilities
│   ├── __init__.py
│   ├── permissions.py              # Role-based DRF permissions
│   ├── pagination.py               # Standard page size
│   ├── mixins.py                   # Reusable view mixins
│   └── exceptions.py               # Custom exception handler
├── scripts/                        # Management scripts & seed data
│   ├── seed_specialties.py
│   └── seed_demo_data.py
├── requirements/
│   ├── base.txt                    # Core dependencies (Django, DRF, JWT, Postgres)
│   ├── local.txt                   # + pytest-django, django-extensions
│   └── production.txt              # + gunicorn, whitenoise, dj-database-url
├── config/                         # Django project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py                 # Common settings (apps, middleware, DRF, JWT)
│   │   ├── local.py                # Dev settings (DEBUG=True, console email)
│   │   └── production.py           # Prod settings (security headers, whitenoise)
│   ├── urls.py                     # Root URLConf — includes all app urls under /api/
│   ├── wsgi.py
│   └── asgi.py
├── Makefile                        # Common commands (run, test, migrate, lint)
├── pytest.ini                      # Test configuration
├── .env.example                    # Environment variable template
├── .gitignore
└── manage.py
```

---

## 2. App Folder Structure

Each app follows this exact pattern. Ownership is strict.

### Example: `apps/users/` (Ahmed)

```
apps/users/
├── __init__.py
├── admin.py              # Custom UserAdmin, PatientProfileAdmin
├── apps.py               # AppConfig with label="users"
├── models.py             # User(AbstractUser), PatientProfile
├── serializers.py        # UserSerializer, RegisterSerializer
├── views.py              # RegisterView, TokenObtainPairView override
├── urls.py               # /api/register/, /api/token/, /api/token/refresh/
└── tests.py              # Auth tests (or tests/ folder if many)
```

### Example: `apps/doctors/` (Abdulazim)

```
apps/doctors/
├── __init__.py
├── admin.py
├── apps.py
├── models.py             # Specialty, DoctorProfile, Availability
├── serializers.py
├── views.py              # DoctorList, DoctorDetail, AvailabilityList
├── urls.py               # /api/doctors/, /api/doctors/<id>/availability/
├── tests.py
└── fixtures/             # specialties.json
```

### Example: `apps/appointments/` (Gerges)

```
apps/appointments/
├── __init__.py
├── admin.py
├── apps.py
├── models.py             # Appointment
├── serializers.py
├── views.py              # PatientAppointmentView, DoctorAppointmentView, AvailabilityManagementView
├── urls.py               # /api/appointments/, /api/doctor/appointments/, /api/doctor/availability/
├── tests.py
└── services.py           # Booking validation, slot release logic (keeps views thin)
```

### Example: `apps/admin_api/` (Mokhtar)

```
apps/admin_api/
├── __init__.py
├── apps.py
├── serializers.py        # AdminUserSerializer, AdminAppointmentSerializer, StatsSerializer
├── views.py              # AdminUserViewSet, AdminAppointmentViewSet, StatsView
├── urls.py               # /api/admin/users/, /api/admin/appointments/, /api/admin/stats/
├── tests.py
└── filters.py            # UserFilter, AppointmentFilter (django-filter)
```

---

## 3. Shared Files & Stewardship

These files are **cross-cutting** — all apps depend on them.

| File | Steward | Why Sacred |
|------|---------|------------|
| `shared/permissions.py` | Ahmed | Every view uses IsDoctor, IsPatient, IsAdmin |
| `shared/pagination.py` | Ahmed | Standard page size affects all list endpoints |
| `shared/mixins.py` | Ahmed | Reusable queryset filtering |
| `shared/exceptions.py` | Ahmed | Custom error format must match frontend ApiError |
| `config/settings/base.py` | Ahmed | DRF, JWT, app registry, middleware |
| `config/settings/local.py` | Ahmed | Dev DB, debug toolbar, console email |
| `config/settings/production.py` | Ahmed | Security headers, whitenoise, ALLOWED_HOSTS |
| `config/urls.py` | Ahmed | Route registry for all apps |
| `Makefile` | Ahmed | Common commands (`make run`, `make test`) |
| `requirements/base.txt` | Ahmed | Core dependencies — affects all apps |

### Stewardship Rules

1. **The steward is the default reviewer** when their file is touched in a PR.
2. **Anyone can read** shared files. No restrictions on reading.
3. **Modifying a shared file:**
   - Announce in team chat before starting work
   - Explain the change and who it affects
   - Open focused PR (or include in feature PR with clear comment)
   - Tag the steward for review
4. **Adding new shared files** (e.g., new utility in `shared/`):
   - Any dev can add, but announce it so others know it exists

---

## 4. Import Hierarchy

Follow this dependency direction to avoid circular imports:

```
Shared (bottom layer)
├── shared/ (permissions, pagination, mixins, exceptions)
├── config/settings/ (base settings)
└── requirements/

Apps (top layer, no cross-imports)
├── apps/users/
├── apps/doctors/
├── apps/appointments/
└── apps/admin_api/
```

**Rule:** Apps can import from shared. Apps should avoid importing from each other directly; use string references in `ForeignKey` / `ManyToManyField` or lazy imports where needed.

**Bad (circular):**
```python
# apps/users/serializers.py
from apps.doctors.serializers import DoctorProfileSerializer  # ❌ WRONG
```

**Good:**
```python
# apps/users/serializers.py
from apps.doctors.models import DoctorProfile  # ✅ OK for models (lazy evaluation)
```

---

## 5. Environment Variables

```bash
# .env.example (committed to repo)
SECRET_KEY=change-me-to-a-50-char-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=medical_booking
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# .env (gitignored, local only)
```

**Rule:** Never commit `.env` with real credentials. `python-dotenv` loads `.env` automatically in `config/settings/base.py`.

---

## 6. Key Commands

| Command | Description |
|---------|-------------|
| `make install` | Install local requirements |
| `make run` | Start development server |
| `make test` | Run Django test suite |
| `make pytest` | Run pytest with coverage |
| `make migrate` | Apply migrations |
| `make makemigrations` | Create migrations |
| `make superuser` | Create admin user |
| `make lint` | Run flake8 |
| `make format` | Run Black formatter |
| `make shell` | Open Django shell |
