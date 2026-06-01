"""
Appointments service layer.

All booking business logic lives here so views stay thin.
See docs/DATABASE_ARCHITECTURE.md §4 for data integrity rules.
"""

from datetime import date as date_type

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.appointments.models import Appointment
from apps.doctors.models import Availability


def book_appointment(*, patient, doctor, date, time):
    """Book a new appointment for a patient with a doctor.

    Uses select_for_update to lock the availability slot and prevent
    race conditions (double-booking at the DB level).

    Args:
        patient: User instance with role=PATIENT.
        doctor: User instance with role=DOCTOR.
        date: datetime.date for the appointment.
        time: datetime.time matching an Availability.start_time.

    Returns:
        Appointment: The newly created Appointment instance.

    Raises:
        ValidationError: If date is in the past or the slot is unavailable.
    """
    if date < date_type.today():
        raise ValidationError({"date": ["Cannot book appointments in the past."]})

    with transaction.atomic():
        try:
            slot = (
                Availability.objects.select_for_update().get(
                    doctor__user=doctor,
                    date=date,
                    start_time=time,
                    is_booked=False,
                )
            )
        except Availability.DoesNotExist:
            raise ValidationError({"time": ["This time slot is no longer available."]})

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            availability=slot,
            date=date,
            time=time,
            status="PENDING",
        )

        slot.is_booked = True
        slot.save(update_fields=["is_booked"])

    return appointment
