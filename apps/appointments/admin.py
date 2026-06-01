"""
Appointments admin configuration.
"""

from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "date", "time", "status"]
    list_filter = ["status", "date"]
    search_fields = ["patient__email", "doctor__email"]
    date_hierarchy = "date"
