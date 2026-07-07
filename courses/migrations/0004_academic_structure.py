import django.db.models.deletion
from django.db import migrations, models


def seed_academic_structure(apps, schema_editor):
    College = apps.get_model("courses", "College")
    Department = apps.get_model("courses", "Department")
    Program = apps.get_model("courses", "Program")
    AcademicYear = apps.get_model("courses", "AcademicYear")
    Semester = apps.get_model("courses", "Semester")
    Section = apps.get_model("courses", "Section")
    Classroom = apps.get_model("courses", "Classroom")
    Course = apps.get_model("courses", "Course")

    college, _ = College.objects.get_or_create(
        name="CPU Business and Information Technology College",
        defaults={"code": "CPU"},
    )
    department, _ = Department.objects.get_or_create(
        name="General Studies",
        defaults={"college": college},
    )
    Department.objects.filter(college__isnull=True).update(college=college)
    program, _ = Program.objects.get_or_create(name="General Program", department=department)
    academic_year, _ = AcademicYear.objects.get_or_create(name="2025/2026", defaults={"is_active": True})
    semester, _ = Semester.objects.get_or_create(
        academic_year=academic_year,
        name="Semester 1",
        defaults={"number": 1, "is_active": True},
    )
    Classroom.objects.get_or_create(name="Room 101", defaults={"capacity": 60, "department": department})

    for item in Program.objects.all():
        Section.objects.get_or_create(
            program=item,
            academic_year=academic_year,
            semester=semester,
            year_level=1,
            name="Section A",
            defaults={"capacity": 60, "is_active": True},
        )

    for course in Course.objects.select_related("program").all():
        course_program = course.program or program
        section = (
            Section.objects.filter(program=course_program, academic_year=academic_year, semester=semester, year_level=1).first()
            or Section.objects.filter(program=course_program).first()
        )
        course.program = course_program
        course.section = section
        course.semester = semester
        course.save(update_fields=["program", "section", "semester"])


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0003_course_program"),
    ]

    operations = [
        migrations.CreateModel(
            name="AcademicYear",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=40, unique=True)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["-is_active", "name"]},
        ),
        migrations.CreateModel(
            name="College",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True)),
                ("code", models.CharField(blank=True, max_length=20)),
                ("address", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="department",
            name="college",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="departments",
                to="courses.college",
            ),
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("number", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="semesters",
                        to="courses.academicyear",
                    ),
                ),
            ],
            options={"ordering": ["academic_year__name", "number", "name"], "unique_together": {("academic_year", "name")}},
        ),
        migrations.CreateModel(
            name="Classroom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("building", models.CharField(blank=True, max_length=120)),
                ("capacity", models.PositiveSmallIntegerField(default=60)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="classrooms",
                        to="courses.department",
                    ),
                ),
            ],
            options={"ordering": ["building", "name"]},
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("year_level", models.PositiveSmallIntegerField(default=1)),
                ("capacity", models.PositiveSmallIntegerField(default=60)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sections",
                        to="courses.academicyear",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="courses.program",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sections",
                        to="courses.semester",
                    ),
                ),
            ],
            options={
                "ordering": ["program__name", "year_level", "name"],
                "unique_together": {("program", "academic_year", "semester", "year_level", "name")},
            },
        ),
        migrations.AddField(
            model_name="course",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="courses",
                to="courses.section",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="semester",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="courses",
                to="courses.semester",
            ),
        ),
        migrations.RunPython(seed_academic_structure, migrations.RunPython.noop),
    ]
