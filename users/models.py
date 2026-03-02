from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		STUDENT = "student", "Student"
		TEACHER = "teacher", "Teacher"
		REGISTRAR = "registrar", "Registrar"
		ADMIN = "admin", "Admin"

	role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
	phone = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return f"{self.username} ({self.role})"
