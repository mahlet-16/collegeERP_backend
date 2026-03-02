from django.db import models

from users.models import User


class Department(models.Model):
	name = models.CharField(max_length=120, unique=True)

	def __str__(self):
		return self.name


class Program(models.Model):
	name = models.CharField(max_length=120)
	department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="programs")

	def __str__(self):
		return self.name


class Course(models.Model):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=200)
	credit_hour = models.PositiveSmallIntegerField(default=3)
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
