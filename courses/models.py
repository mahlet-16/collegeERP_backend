from django.db import models

from users.models import User


class College(models.Model):
	name = models.CharField(max_length=160, unique=True)
	code = models.CharField(max_length=20, blank=True)
	address = models.CharField(max_length=255, blank=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Department(models.Model):
	name = models.CharField(max_length=120, unique=True)
	college = models.ForeignKey(
		College,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="departments",
	)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Program(models.Model):
	name = models.CharField(max_length=120)
	department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="programs")

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class AcademicYear(models.Model):
	name = models.CharField(max_length=40, unique=True)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["-is_active", "name"]

	def __str__(self):
		return self.name


class Semester(models.Model):
	name = models.CharField(max_length=60)
	academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
	number = models.PositiveSmallIntegerField(default=1)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["academic_year__name", "number", "name"]
		unique_together = ("academic_year", "name")

	def __str__(self):
		return f"{self.academic_year.name} - {self.name}"


class Section(models.Model):
	name = models.CharField(max_length=80)
	program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="sections")
	academic_year = models.ForeignKey(
		AcademicYear,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="sections",
	)
	semester = models.ForeignKey(
		Semester,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="sections",
	)
	year_level = models.PositiveSmallIntegerField(default=1)
	capacity = models.PositiveSmallIntegerField(default=60)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["program__name", "year_level", "name"]
		unique_together = ("program", "academic_year", "semester", "year_level", "name")

	@property
	def label(self):
		return f"{self.program.name} Year {self.year_level} {self.name}"

	def __str__(self):
		return self.label


class Classroom(models.Model):
	name = models.CharField(max_length=80, unique=True)
	building = models.CharField(max_length=120, blank=True)
	capacity = models.PositiveSmallIntegerField(default=60)
	department = models.ForeignKey(
		Department,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="classrooms",
	)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["building", "name"]

	def __str__(self):
		return self.name


def get_default_academic_structure():
	college, _ = College.objects.get_or_create(
		name="CPU Business and Information Technology College",
		defaults={"code": "CPU"},
	)
	department, _ = Department.objects.get_or_create(
		name="General Studies",
		defaults={"college": college},
	)
	if department.college_id is None:
		department.college = college
		department.save(update_fields=["college"])
	program, _ = Program.objects.get_or_create(name="General Program", department=department)
	academic_year, _ = AcademicYear.objects.get_or_create(name="2025/2026", defaults={"is_active": True})
	semester, _ = Semester.objects.get_or_create(
		academic_year=academic_year,
		name="Semester 1",
		defaults={"number": 1, "is_active": True},
	)
	section, _ = Section.objects.get_or_create(
		program=program,
		academic_year=academic_year,
		semester=semester,
		year_level=1,
		name="Section A",
		defaults={"capacity": 60, "is_active": True},
	)
	classroom, _ = Classroom.objects.get_or_create(name="Room 101", defaults={"capacity": 60, "department": department})
	return {
		"college": college,
		"department": department,
		"program": program,
		"academic_year": academic_year,
		"semester": semester,
		"section": section,
		"classroom": classroom,
	}


def get_default_section():
	return get_default_academic_structure()["section"]


class Course(models.Model):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=200)
	credit_hour = models.PositiveSmallIntegerField(default=3)
	program = models.ForeignKey(
		Program,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="courses",
	)
	section = models.ForeignKey(
		Section,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="courses",
	)
	semester = models.ForeignKey(
		Semester,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="courses",
	)
	teacher = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="teaching_courses",
		limit_choices_to={"role": "teacher"},
	)

	def __str__(self):
		return f"{self.code} - {self.name}"


class Enrollment(models.Model):
	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="enrollments",
		limit_choices_to={"role": "student"},
	)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
	term = models.CharField(max_length=50)

	class Meta:
		unique_together = ("student", "course", "term")

	def __str__(self):
		return f"{self.student.username} -> {self.course.code} ({self.term})"
