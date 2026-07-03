from django.db import migrations, models


def blank_ids_to_null(apps, schema_editor):
    StudentProfile = apps.get_model("users", "StudentProfile")
    TeacherProfile = apps.get_model("users", "TeacherProfile")
    StudentProfile.objects.filter(student_id="").update(student_id=None)
    TeacherProfile.objects.filter(staff_id="").update(staff_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_profiles_notifications_audit_settings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="studentprofile",
            name="student_id",
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="teacherprofile",
            name="staff_id",
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
        migrations.RunPython(blank_ids_to_null, migrations.RunPython.noop),
    ]
