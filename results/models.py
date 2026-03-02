from django.db import models

from courses.models import Course
from users.models import User


class Result(models.Model):
	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="results",
		limit_choices_to={"role": "student"},
	)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
	mark = models.DecimalField(max_digits=5, decimal_places=2)
	grade = models.CharField(max_length=5)
	gpa = models.DecimalField(max_digits=3, decimal_places=2)
	term = models.CharField(max_length=50)
	entered_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name="entered_results",
		limit_choices_to={"role": "teacher"},
	)
	published = models.BooleanField(default=False)

	class Meta:
		unique_together = ("student", "course", "term")

	def __str__(self):
		return f"{self.student.username} {self.course.code} {self.grade}"
