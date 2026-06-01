# Standard library
import random
from datetime import date, time, timedelta

# Django
from django.core.management.base import BaseCommand
from django.db import transaction

# Local / project imports
from apps.users.models import User
from apps.doctors.models import DoctorProfile, Specialty, Availability
from apps.appointments.models import Appointment

# ---------------------------------------------------------------------------
# Static seed data pools
# ---------------------------------------------------------------------------

ADMIN_USERS = [
    {"first_name": "Super",   "last_name": "Admin",   "email": "admin@clinic.com"},
    {"first_name": "Mohamed", "last_name": "Ibrahim",  "email": "m.ibrahim@clinic.com"},
]

DOCTOR_DATA = [
    {
        "first_name": "Sarah",   "last_name": "Chen",
        "email": "sarah.chen@clinic.com",
        "specialty": "Cardiology",
        "bio": "Board-certified cardiologist with 12 years of experience in interventional cardiology.",
        "image_url": "https://i.pravatar.cc/150?u=sarah",
        "phone": "01001000001",
    },
    {
        "first_name": "Ahmed",   "last_name": "Hassan",
        "email": "ahmed.hassan@clinic.com",
        "specialty": "Neurology",
        "bio": "Specialist in neurodegenerative diseases and stroke rehabilitation.",
        "image_url": "https://i.pravatar.cc/150?u=ahmed",
        "phone": "01001000002",
    },
    {
        "first_name": "Layla",   "last_name": "Nasser",
        "email": "layla.nasser@clinic.com",
        "specialty": "Dermatology",
        "bio": "Expert in medical and cosmetic dermatology with a focus on skin cancer screening.",
        "image_url": "https://i.pravatar.cc/150?u=layla",
        "phone": "01001000003",
    },
    {
        "first_name": "Omar",    "last_name": "Khalil",
        "email": "omar.khalil@clinic.com",
        "specialty": "Pediatrics",
        "bio": "Dedicated pediatrician with 8 years caring for newborns through adolescents.",
        "image_url": "https://i.pravatar.cc/150?u=omar",
        "phone": "01001000004",
    },
    {
        "first_name": "Nour",    "last_name": "Farouk",
        "email": "nour.farouk@clinic.com",
        "specialty": "Orthopedics",
        "bio": "Orthopedic surgeon specialising in sports injuries and joint replacement.",
        "image_url": "https://i.pravatar.cc/150?u=nour",
        "phone": "01001000005",
    },
]

PATIENT_DATA = [
    {"first_name": "John",    "last_name": "Doe",      "email": "john.doe@mail.com"},
    {"first_name": "Fatima",  "last_name": "Ali",      "email": "fatima.ali@mail.com"},
    {"first_name": "Carlos",  "last_name": "Gomez",    "email": "carlos.gomez@mail.com"},
    {"first_name": "Aya",     "last_name": "Mostafa",  "email": "aya.mostafa@mail.com"},
    {"first_name": "James",   "last_name": "Wilson",   "email": "james.wilson@mail.com"},
    {"first_name": "Mona",    "last_name": "Samir",    "email": "mona.samir@mail.com"},
    {"first_name": "Liam",    "last_name": "Brown",    "email": "liam.brown@mail.com"},
    {"first_name": "Hana",    "last_name": "Youssef",  "email": "hana.youssef@mail.com"},
    {"first_name": "Noah",    "last_name": "Taylor",   "email": "noah.taylor@mail.com"},
    {"first_name": "Salma",   "last_name": "Kamel",    "email": "salma.kamel@mail.com"},
]

# Appointment time slots matching real availability patterns
TIME_SLOTS = [
    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
    time(11, 0), time(11, 30), time(13, 0), time(13, 30),
    time(14, 0), time(14, 30), time(15, 0), time(15, 30),
]

# Weighted statuses: past appointments lean COMPLETED/CANCELLED,
# future appointments lean PENDING/CONFIRMED
PAST_STATUSES   = ["COMPLETED", "COMPLETED", "COMPLETED", "CANCELLED"]
FUTURE_STATUSES = ["PENDING", "PENDING", "CONFIRMED", "CONFIRMED"]

DOCTOR_NOTES = [
    "Please bring all previous test results.",
    "Arrive 15 minutes early for paperwork.",
    "Fasting required for 8 hours before the appointment.",
    None,
    None,
]


class Command(BaseCommand):
    """Seed the database with realistic demo data for local development.

    Purges existing non-admin users, doctor profiles, availability slots,
    and appointments before inserting fresh records. Safe to run multiple
    times (idempotent).

    Usage:
        python manage.py seed_demo_data
    """

    help = "Seed demo users, doctors, patients, and appointments for local development."

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        self.stdout.write("\n🌱 Starting demo data seed...\n")

        with transaction.atomic():
            self._purge_existing_data()
            specialties = self._seed_specialties()
            admins      = self._seed_admins()
            doctors     = self._seed_doctors(specialties)
            patients    = self._seed_patients()
            self._seed_appointments(doctors, patients)

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeded successfully!\n"))
        self._print_credentials()

    # ------------------------------------------------------------------
    # Step 1 — Purge
    # ------------------------------------------------------------------

    def _purge_existing_data(self):
        self.stdout.write("🗑️  Purging existing demo data...")

        # Delete in reverse FK dependency order
        deleted_appts, _ = Appointment.objects.all().delete()
        deleted_avail, _ = Availability.objects.all().delete()
        deleted_docs,  _ = DoctorProfile.objects.all().delete()

        # Remove non-admin users (admins are safe to recreate by email)
        deleted_users, _ = User.objects.filter(
            role__in=["DOCTOR", "PATIENT"]
        ).delete()

        # Also remove admin seed accounts so they can be re-created cleanly
        User.objects.filter(
            email__in=[a["email"] for a in ADMIN_USERS]
        ).delete()

        self.stdout.write(
            f"   Removed: {deleted_appts} appointments, "
            f"{deleted_avail} availability slots, "
            f"{deleted_docs} doctor profiles, "
            f"{deleted_users} users."
        )

    # ------------------------------------------------------------------
    # Step 2 — Specialties
    # ------------------------------------------------------------------

    def _seed_specialties(self) -> dict[str, Specialty]:
        """Ensure all required specialties exist; return name→object map."""
        self.stdout.write("🏥  Ensuring specialties exist...")

        names = [
            "Cardiology", "Neurology", "Dermatology",
            "Pediatrics", "Orthopedics", "General Practice",
        ]
        specialty_map = {}
        for name in names:
            obj, created = Specialty.objects.get_or_create(name=name)
            specialty_map[name] = obj
            if created:
                self.stdout.write(f"   + Specialty created: {name}")

        self.stdout.write(f"   {len(specialty_map)} specialties ready.")
        return specialty_map

    # ------------------------------------------------------------------
    # Step 3 — Admins
    # ------------------------------------------------------------------

    def _seed_admins(self) -> list[User]:
        self.stdout.write("👤  Creating admin users...")
        admins = []

        for data in ADMIN_USERS:
            user = User(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role="ADMIN",
                is_active=True,
                is_approved=True,
                is_staff=True,
                is_superuser=True,
            )
            user.set_password("admin123")
            user.save()
            admins.append(user)
            self.stdout.write(f"   + Admin: {user.email}")

        return admins

    # ------------------------------------------------------------------
    # Step 4 — Doctors
    # ------------------------------------------------------------------

    def _seed_doctors(self, specialty_map: dict) -> list[DoctorProfile]:
        self.stdout.write("🩺  Creating doctor profiles...")
        profiles = []

        for data in DOCTOR_DATA:
            # Create the User account
            user = User(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role="DOCTOR",
                is_active=True,
                is_approved=True,
            )
            user.set_password("doctor123")
            user.save()

            # Create DoctorProfile linked to that user
            profile = DoctorProfile.objects.create(
                user=user,
                specialty=specialty_map[data["specialty"]],
                bio=data["bio"],
                image_url=data["image_url"],
                phone=data["phone"],
            )

            # Seed availability: next 14 days, 4 random slots per day
            self._seed_availability_for_doctor(profile)

            profiles.append(profile)
            self.stdout.write(
                f"   + Dr. {user.first_name} {user.last_name} "
                f"({data['specialty']})"
            )

        return profiles

    def _seed_availability_for_doctor(self, profile: DoctorProfile) -> None:
        """Create 4 random availability slots per day for the next 14 days."""
        today = date.today()
        slots_to_create = []

        for day_offset in range(1, 15):  # tomorrow → 14 days ahead
            slot_date = today + timedelta(days=day_offset)
            chosen_times = random.sample(TIME_SLOTS, k=4)

            for slot_time in chosen_times:
                end_time = time(slot_time.hour + 1, slot_time.minute)
                slots_to_create.append(
                    Availability(
                        doctor=profile,
                        date=slot_date,
                        start_time=slot_time,
                        end_time=end_time,
                        is_booked=False,
                    )
                )

        Availability.objects.bulk_create(slots_to_create)

    # ------------------------------------------------------------------
    # Step 5 — Patients
    # ------------------------------------------------------------------

    def _seed_patients(self) -> list[User]:
        self.stdout.write("🧑‍⚕️  Creating patient accounts...")
        patients = []

        for data in PATIENT_DATA:
            user = User(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role="PATIENT",
                is_active=True,
                is_approved=True,
            )
            user.set_password("patient123")
            user.save()
            patients.append(user)
            self.stdout.write(f"   + Patient: {user.email}")

        return patients

    # ------------------------------------------------------------------
    # Step 6 — Appointments
    # ------------------------------------------------------------------

    def _seed_appointments(
        self,
        doctors: list[DoctorProfile],
        patients: list[User],
    ) -> None:
        """Create 20+ appointments spread across past and future dates."""
        self.stdout.write("📅  Creating appointments...")

        today = date.today()
        appointments_to_create = []

        # 12 past appointments (30 → 1 days ago)
        for _ in range(12):
            days_ago  = random.randint(1, 30)
            appt_date = today - timedelta(days=days_ago)
            doctor    = random.choice(doctors)
            patient   = random.choice(patients)
            slot_time = random.choice(TIME_SLOTS)
            status    = random.choice(PAST_STATUSES)

            appointments_to_create.append(
                Appointment(
                    patient=patient,
                    doctor=doctor.user,
                    date=appt_date,
                    time=slot_time,
                    status=status,
                    notes=random.choice(DOCTOR_NOTES),
                )
            )

        # 10 future appointments (1 → 14 days ahead)
        for _ in range(10):
            days_ahead = random.randint(1, 14)
            appt_date  = today + timedelta(days=days_ahead)
            doctor     = random.choice(doctors)
            patient    = random.choice(patients)
            status     = random.choice(FUTURE_STATUSES)

            # Try to find a free availability slot for this doctor/date
            availability = (
                Availability.objects
                .filter(doctor=doctor, date=appt_date, is_booked=False)
                .first()
            )

            if availability:
                slot_time               = availability.start_time
                availability.is_booked  = True
                availability.save()
            else:
                slot_time = random.choice(TIME_SLOTS)

            appointments_to_create.append(
                Appointment(
                    patient=patient,
                    doctor=doctor.user,
                    availability=availability,
                    date=appt_date,
                    time=slot_time,
                    status=status,
                    notes=random.choice(DOCTOR_NOTES),
                )
            )

        Appointment.objects.bulk_create(appointments_to_create)
        self.stdout.write(
            f"   {len(appointments_to_create)} appointments created "
            f"(12 past, 10 future)."
        )

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------

    def _print_credentials(self) -> None:
        self.stdout.write("\n" + "─" * 50)
        self.stdout.write(self.style.WARNING("🔑  Demo Login Credentials"))
        self.stdout.write("─" * 50)
        self.stdout.write("  ADMINS   → admin@clinic.com / admin123")
        self.stdout.write("           → m.ibrahim@clinic.com / admin123")
        self.stdout.write("  DOCTORS  → sarah.chen@clinic.com / doctor123")
        self.stdout.write("           → ahmed.hassan@clinic.com / doctor123")
        self.stdout.write("           → (and 3 more doctors)")
        self.stdout.write("  PATIENTS → john.doe@mail.com / patient123")
        self.stdout.write("           → fatima.ali@mail.com / patient123")
        self.stdout.write("           → (and 8 more patients)")
        self.stdout.write("─" * 50 + "\n")