from django.db import models

from courses.models import Course
from users.models import User


class Attendance(models.Model):
	class Status(models.TextChoices):
		PRESENT = "present", "Present"
		ABSENT = "absent", "Absent"
		LATE = "late", "Late"
		EXCUSED = "excused", "Excused"

	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="attendance_records",
		limit_choices_to={"role": "student"},
	)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_records")
	date = models.DateField()
	status = models.CharField(max_length=10, choices=Status.choices)
	comment = models.CharField(max_length=255, blank=True)
	recorded_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name="recorded_attendance",
		limit_choices_to={"role": "teacher"},
	)

	class Meta:
		unique_together = ("student", "course", "date")

	def __str__(self):
		return f"{self.student.username} {self.course.code} {self.date} {self.status}"
