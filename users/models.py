from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


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


class StudentProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="student_profile",
		limit_choices_to={"role": User.Role.STUDENT},
	)
	program = models.ForeignKey(
		"courses.Program",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="students",
	)
	student_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
	level = models.CharField(max_length=40, blank=True)
	address = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return self.student_id or self.user.username


class TeacherProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="teacher_profile",
		limit_choices_to={"role": User.Role.TEACHER},
	)
	staff_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
	department = models.ForeignKey(
		"courses.Department",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="teachers",
	)
	office = models.CharField(max_length=80, blank=True)

	def __str__(self):
		return self.staff_id or self.user.username


class Notification(models.Model):
	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notifications",
	)
	title = models.CharField(max_length=160)
	message = models.TextField()
	read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.recipient.username}: {self.title}"


class AuditLog(models.Model):
	actor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="audit_events",
	)
	action = models.CharField(max_length=120)
	model_name = models.CharField(max_length=120, blank=True)
	object_id = models.CharField(max_length=80, blank=True)
	detail = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.action} by {self.actor or 'system'}"


class SystemSetting(models.Model):
	key = models.CharField(max_length=80, unique=True)
	value = models.JSONField(default=dict, blank=True)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="updated_settings",
	)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.key
