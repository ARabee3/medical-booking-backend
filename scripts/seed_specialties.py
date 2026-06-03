#!/usr/bin/env python3
"""Standalone script to seed the 6 core medical specialties.

Usage:
    python scripts/seed_specialties.py

This script is safe to run multiple times — existing specialties are skipped.
"""

import os
import sys

# Ensure Django settings are available
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import django  # noqa: E402

django.setup()

from apps.doctors.models import Specialty  # noqa: E402


SPECIALTIES = [
    {
        "name": "Cardiology",
        "description": "Diagnosis and treatment of heart conditions, including arrhythmias, heart failure, and coronary artery disease.",
        "icon": "heart-pulse",
    },
    {
        "name": "Dermatology",
        "description": "Diagnosis and treatment of skin, hair, and nail conditions, including eczema, psoriasis, and skin cancer screening.",
        "icon": "shield",
    },
    {
        "name": "Neurology",
        "description": "Diagnosis and management of disorders of the nervous system, including stroke, epilepsy, and neurodegenerative diseases.",
        "icon": "brain",
    },
    {
        "name": "Pediatrics",
        "description": "Comprehensive medical care for infants, children, and adolescents, including preventive care and developmental assessments.",
        "icon": "baby",
    },
    {
        "name": "Orthopedics",
        "description": "Diagnosis and treatment of musculoskeletal conditions, including fractures, joint replacements, and sports injuries.",
        "icon": "bone",
    },
    {
        "name": "General Practice",
        "description": "Primary healthcare for patients of all ages, covering preventive care, chronic disease management, and acute illness treatment.",
        "icon": "stethoscope",
    },
]


def seed_specialties() -> None:
    """Create specialty records if they don't already exist."""
    created_count = 0
    for spec_data in SPECIALTIES:
        obj, created = Specialty.objects.get_or_create(
            name=spec_data["name"],
            defaults={
                "description": spec_data["description"],
                "icon": spec_data["icon"],
            },
        )
        if created:
            created_count += 1
            print(f"  + Created specialty: {obj.name}")
        else:
            print(f"  = Already exists: {obj.name}")

    print(f"\nDone. {created_count} new specialty(s) created.")


if __name__ == "__main__":
    seed_specialties()
