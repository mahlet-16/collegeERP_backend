from django.db import models

from courses.models import Course
from users.models import User


class TimetableEntry(models.Model):
	class Day(models.TextChoices):
		MONDAY = "monday", "Monday"
		TUESDAY = "tuesday", "Tuesday"
		WEDNESDAY = "wednesday", "Wednesday"
		THURSDAY = "thursday", "Thursday"
		FRIDAY = "friday", "Friday"
		SATURDAY = "saturday", "Saturday"

	term = models.CharField(max_length=50)
	day = models.CharField(max_length=12, choices=Day.choices)
	start_time = models.TimeField()
	end_time = models.TimeField()
	room = models.CharField(max_length=50)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="timetable_entries")
	assigned_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name="published_timetables",
		limit_choices_to={"role": "registrar"},
	)
	published = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.course.code} {self.day} {self.start_time}-{self.end_time}"


class ExamSchedule(models.Model):
	term = models.CharField(max_length=50)
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()
	room = models.CharField(max_length=50)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
	description = models.CharField(max_length=120, blank=True)
	scheduled_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name="scheduled_exams",
		limit_choices_to={"role__in": [User.Role.REGISTRAR, User.Role.ADMIN]},
	)
	published = models.BooleanField(default=False)

	class Meta:
		ordering = ["date", "start_time"]

	def __str__(self):
		return f"Exam {self.course.code} on {self.date} {self.start_time}-{self.end_time}"
