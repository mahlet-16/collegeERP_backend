import django.db.models.deletion
from django.db import migrations, models


def backfill_student_sections(apps, schema_editor):
    StudentProfile = apps.get_model("users", "StudentProfile")
    Section = apps.get_model("courses", "Section")

    default_section = Section.objects.select_related("program").first()
    if not default_section:
        return

    for profile in StudentProfile.objects.filter(section__isnull=True):
        profile.section = default_section
        if profile.program_id is None:
            profile.program = default_section.program
        if not profile.level:
            profile.level = f"Year {default_section.year_level}"
        profile.save(update_fields=["section", "program", "level"])


class Migration(migrations.Migration):
    atomic = False


    dependencies = [
        ("courses", "0004_academic_structure"),
        ("users", "0003_unique_profile_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="avatar_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="students",
                to="courses.section",
            ),
        ),
        migrations.RunPython(backfill_student_sections, migrations.RunPython.noop),
    ]
