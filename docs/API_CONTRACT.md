# API Contract (Backend Implementation Reference)

**Status:** Backend implementation guide. All Django endpoints must match these contracts exactly.

**Base URL:** `/api`

---

## Authentication

### POST /api/register/

Register a new user.

**Request:**
```json
{
  "email": "patient@example.com",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "role": "PATIENT",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response 201:**
```json
{
  "user": {
    "id": 1,
    "email": "patient@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "PATIENT",
    "is_active": true
  },
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 400:**
```json
{
  "email": ["User with this email already exists."],
  "password": ["Passwords do not match."]
}
```

---

### POST /api/token/

Login and receive JWT pair.

**Request:**
```json
{
  "email": "patient@example.com",
  "password": "securepass123"
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 401:**
```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### POST /api/token/refresh/

Refresh access token.

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 401:**
```json
{
  "detail": "Token is invalid or expired"
}
```

---

## Doctors

### GET /api/doctors/

List all approved doctors.

**Query Parameters:**
- `specialty` (optional): Filter by specialty string
- `search` (optional): Search by name

**Response 200:**
```json
[
  {
    "id": 1,
    "user_id": 2,
    "name": "Dr. Sarah Chen",
    "email": "sarah.chen@hospital.com",
    "specialty": "Cardiology",
    "bio": "Board-certified cardiologist with 12 years of experience in interventional cardiology.",
    "image_url": "https://i.pravatar.cc/150?u=sarah",
    "is_active": true
  }
]
```

---

### GET /api/doctors/:id/

Get single doctor profile.

**Response 200:**
```json
{
  "id": 1,
  "user_id": 2,
  "name": "Dr. Sarah Chen",
  "email": "sarah.chen@hospital.com",
  "specialty": "Cardiology",
  "bio": "Board-certified cardiologist with 12 years of experience in interventional cardiology.",
  "image_url": "https://i.pravatar.cc/150?u=sarah",
  "is_active": true
}
```

**Response 404:**
```json
{
  "detail": "Doctor not found"
}
```

---

### GET /api/doctors/:id/availability/

Get available slots for a doctor on a specific date.

**Query Parameters:**
- `date` (required): `YYYY-MM-DD` format

**Response 200:**
```json
{
  "doctor_id": 1,
  "date": "2026-01-20",
  "slots": [
    "09:00",
    "10:30",
    "14:00",
    "15:30"
  ]
}
```

**Response 200 (no availability):**
```json
{
  "doctor_id": 1,
  "date": "2026-01-20",
  "slots": []
}
```

---

## Appointments (Patient)

### GET /api/appointments/

List current patient's appointments.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
[
  {
    "id": 1,
    "doctor": {
      "id": 1,
      "name": "Dr. Sarah Chen",
      "specialty": "Cardiology",
      "image_url": "https://i.pravatar.cc/150?u=sarah"
    },
    "date": "2026-01-20",
    "time": "09:00",
    "status": "CONFIRMED",
    "notes": null,
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

---

### POST /api/appointments/

Book a new appointment.

**Request:**
```json
{
  "doctor_id": 1,
  "date": "2026-01-20",
  "time": "09:00"
}
```

**Response 201:**
```json
{
  "id": 1,
  "doctor": {
    "id": 1,
    "name": "Dr. Sarah Chen",
    "specialty": "Cardiology"
  },
  "date": "2026-01-20",
  "time": "09:00",
  "status": "PENDING",
  "notes": null,
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Response 400 (slot taken):**
```json
{
  "time": ["This time slot is no longer available."]
}
```

**Response 400 (past date):**
```json
{
  "date": ["Cannot book appointments in the past."]
}
```

---

### PATCH /api/appointments/:id/

Update appointment (cancel or reschedule).

**Request (cancel):**
```json
{
  "status": "CANCELLED"
}
```

**Request (reschedule):**
```json
{
  "date": "2026-01-22",
  "time": "14:00"
}
```

**Response 200:** Returns updated appointment.

**Response 403:**
```json
{
  "detail": "You do not have permission to modify this appointment"
}
```

---

## Doctor Endpoints

### GET /api/doctor/appointments/

Get appointments for the authenticated doctor.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
[
  {
    "id": 1,
    "patient": {
      "id": 3,
      "name": "John Doe",
      "email": "patient@example.com"
    },
    "date": "2026-01-20",
    "time": "09:00",
    "status": "PENDING",
    "notes": null,
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

---

### PATCH /api/doctor/appointments/:id/

Doctor approves/rejects an appointment.

**Request:**
```json
{
  "status": "CONFIRMED",
  "notes": "Please arrive 15 minutes early for paperwork."
}
```

**Response 200:** Returns updated appointment.

**Response 403:** "You can only manage your own appointments."

---

### POST /api/doctor/availability/

Add availability slot.

**Request:**
```json
{
  "date": "2026-01-20",
  "start_time": "09:00",
  "end_time": "10:00"
}
```

**Response 201:**
```json
{
  "id": 1,
  "date": "2026-01-20",
  "start_time": "09:00",
  "end_time": "10:00",
  "is_booked": false
}
```

---

### DELETE /api/doctor/availability/:id/

Remove availability slot.

**Response 204:** No content

**Response 400:**
```json
{
  "detail": "Cannot delete a slot that is already booked"
}
```

---

## Admin Endpoints

### GET /api/admin/users/

List all users.

**Response 200:**
```json
[
  {
    "id": 1,
    "email": "patient@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "PATIENT",
    "is_active": true,
    "is_approved": true,
    "date_joined": "2026-01-10"
  }
]
```

---

### PATCH /api/admin/users/:id/

Update user status.

**Request:**
```json
{
  "is_active": false,
  "is_approved": true
}
```

**Response 200:** Returns updated user.

---

### GET /api/admin/appointments/

List all system appointments.

**Query Parameters:**
- `status` (optional): PENDING, CONFIRMED, COMPLETED, CANCELLED
- `date_from` (optional): `YYYY-MM-DD`
- `date_to` (optional): `YYYY-MM-DD`

**Response 200:** Array of appointments with full doctor and patient objects.

---

## Global Types (Reference for Serializers)

```python
# Serializers should produce these shapes

UserRole = 'ADMIN' | 'DOCTOR' | 'PATIENT'
AppointmentStatus = 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED'
```

---

## Backend Implementation Notes

- All list endpoints use `StandardResultsSetPagination` (page_size=20).
- All endpoints return JSON with `application/json` content type.
- Validation errors return 400 with field-level messages.
- Permission errors return 403 with `{"detail": "..."}`.
- Not found errors return 404 with `{"detail": "Not found."}`.
- Date and time formats in JSON: `YYYY-MM-DD` and `HH:mm`.
- Timestamps in JSON: ISO 8601 strings.
