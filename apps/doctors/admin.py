"""
Doctors admin configuration.
"""

from django.contrib import admin
from .models import Specialty, DoctorProfile, Availability


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "specialty", "phone"]
    list_filter = ["specialty", "user__is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "start_time", "end_time", "is_booked"]
    list_filter = ["date", "is_booked"]
    search_fields = ["doctor__user__email"]
