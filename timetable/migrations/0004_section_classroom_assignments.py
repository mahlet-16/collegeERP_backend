import django.db.models.deletion
from django.db import migrations, models


def backfill_schedule_assignments(apps, schema_editor):
    Classroom = apps.get_model("courses", "Classroom")
    TimetableEntry = apps.get_model("timetable", "TimetableEntry")
    ExamSchedule = apps.get_model("timetable", "ExamSchedule")

    for model in (TimetableEntry, ExamSchedule):
        for item in model.objects.select_related("course", "course__section").all():
            room_name = item.room or "Room 101"
            classroom, _ = Classroom.objects.get_or_create(name=room_name, defaults={"capacity": 60})
            item.section = item.course.section
            item.classroom = classroom
            item.save(update_fields=["section", "classroom"])


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_academic_structure"),
        ("timetable", "0003_examschedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="examschedule",
            name="classroom",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="exams",
                to="courses.classroom",
            ),
        ),
        migrations.AddField(
            model_name="examschedule",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="exams",
                to="courses.section",
            ),
        ),
        migrations.AddField(
            model_name="timetableentry",
            name="classroom",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="timetable_entries",
                to="courses.classroom",
            ),
        ),
        migrations.AddField(
            model_name="timetableentry",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="timetable_entries",
                to="courses.section",
            ),
        ),
        migrations.RunPython(backfill_schedule_assignments, migrations.RunPython.noop),
    ]
