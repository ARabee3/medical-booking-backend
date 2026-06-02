"""
Appointments admin configuration.
"""

from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin configuration for the Appointment model."""

    list_display = ["id", "patient", "doctor", "date", "time", "status", "created_at"]
    list_filter = ["status", "date"]
    search_fields = ["patient__email", "doctor__email"]
    date_hierarchy = "date"
    ordering = ["-date", "-created_at"]
    readonly_fields = ["created_at", "updated_at"]
    list_select_related = ["patient", "doctor"]
