"""
Users admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "role", "is_active", "is_approved", "date_joined"]
    list_filter = ["role", "is_active", "is_approved", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Approval", {"fields": ("role", "is_approved")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role & Approval", {"fields": ("role", "is_approved")}),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "date_of_birth"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
