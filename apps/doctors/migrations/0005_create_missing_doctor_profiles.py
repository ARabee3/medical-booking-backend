# Generated manually — creates DoctorProfile for existing doctors missing one.

from django.db import migrations, transaction


def create_missing_doctor_profiles(apps, schema_editor):
    User = apps.get_model("users", "User")
    DoctorProfile = apps.get_model("doctors", "DoctorProfile")

    doctor_ids = set(
        User.objects.filter(role="DOCTOR")
        .exclude(id__in=DoctorProfile.objects.values("user_id"))
        .values_list("id", flat=True)
    )

    profiles = [DoctorProfile(user_id=uid) for uid in doctor_ids]

    if profiles:
        with transaction.atomic():
            DoctorProfile.objects.bulk_create(profiles)
        print(f"Created {len(profiles)} missing DoctorProfile(s).")


def reverse_migration(apps, schema_editor):
    # No-op: we don't want to delete profiles on reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("doctors", "0004_availability_price"),
    ]

    operations = [
        migrations.RunPython(
            create_missing_doctor_profiles,
            reverse_migration,
        ),
    ]
