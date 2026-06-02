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


def cancel_appointment(*, appointment):
    """Cancel an existing appointment and release its availability slot.

    If the appointment is linked to an Availability slot, that slot is
    freed (is_booked=False) so other patients can book it again.

    Args:
        appointment: The Appointment instance to cancel.

    Returns:
        Appointment: The updated appointment with status=CANCELLED.
    """
    with transaction.atomic():
        if appointment.availability_id:
            Availability.objects.filter(id=appointment.availability_id).update(
                is_booked=False
            )

        appointment.status = "CANCELLED"
        appointment.availability = None
        appointment.save()

    return appointment


def reschedule_appointment(*, appointment, new_date, new_time):
    """Reschedule an appointment to a new date/time slot.

    Atomically releases the old slot and books the new one.
    Validates the new slot is available and not in the past.

    Args:
        appointment: The Appointment instance to reschedule.
        new_date: datetime.date for the new appointment.
        new_time: datetime.time matching a new Availability.start_time.

    Returns:
        Appointment: The updated appointment.

    Raises:
        ValidationError: If new date is in the past or new slot is unavailable.
    """
    if new_date < date_type.today():
        raise ValidationError({"date": ["Cannot book appointments in the past."]})

    with transaction.atomic():
        try:
            new_slot = Availability.objects.select_for_update().get(
                doctor__user=appointment.doctor,
                date=new_date,
                start_time=new_time,
                is_booked=False,
            )
        except Availability.DoesNotExist:
            raise ValidationError({"time": ["This time slot is no longer available."]})

        # Release the old slot before booking the new one
        if appointment.availability_id:
            Availability.objects.filter(id=appointment.availability_id).update(
                is_booked=False
            )

        new_slot.is_booked = True
        new_slot.save(update_fields=["is_booked"])

        appointment.date = new_date
        appointment.time = new_time
        appointment.availability = new_slot
        appointment.save()

    return appointment
