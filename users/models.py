from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


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
	section = models.ForeignKey(
		"courses.Section",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="students",
	)
	student_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
	level = models.CharField(max_length=40, blank=True)
	address = models.CharField(max_length=255, blank=True)
	emergency_contact = models.CharField(max_length=40, blank=True)
	avatar_url = models.URLField(blank=True)

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


def generated_profile_id(prefix, model, field_name, user_id):
	candidate = f"{prefix}-{user_id:05d}"
	suffix = 1
	while model.objects.filter(**{field_name: candidate}).exists():
		suffix += 1
		candidate = f"{prefix}-{user_id:05d}-{suffix}"
	return candidate


def sync_user_role_profile(user):
	"""Keep role-specific profiles aligned with the current user role."""
	if user.role == User.Role.STUDENT:
		try:
			from courses.models import get_default_section
			default_section = get_default_section()
		except Exception:
			default_section = None
		StudentProfile.objects.get_or_create(
			user=user,
			defaults={
				"student_id": generated_profile_id("STU", StudentProfile, "student_id", user.id),
				"section": default_section,
				"program": getattr(default_section, "program", None),
				"level": f"Year {getattr(default_section, 'year_level', 1)}" if default_section else "",
			},
		)
		TeacherProfile.objects.filter(user=user).delete()
		return

	if user.role == User.Role.TEACHER:
		TeacherProfile.objects.get_or_create(
			user=user,
			defaults={"staff_id": generated_profile_id("TCH", TeacherProfile, "staff_id", user.id)},
		)
		StudentProfile.objects.filter(user=user).delete()
		return

	StudentProfile.objects.filter(user=user).delete()
	TeacherProfile.objects.filter(user=user).delete()

	try:
		from courses.models import Course
	except Exception:
		return
	Course.objects.filter(teacher=user).update(teacher=None)


@receiver(post_save, sender=User)
def ensure_role_profile(sender, instance, **kwargs):
	sync_user_role_profile(instance)


@receiver(post_save, sender='courses.Course')
def notify_course_assignment(sender, instance, created, **kwargs):
	if instance.teacher:
		try:
			title = "New Course Assigned"
			message = f"You have been assigned to teach the course: {instance.name} ({instance.code})."
			notif_exists = Notification.objects.filter(
				recipient=instance.teacher,
				title=title,
				message=message
			).exists()
			if not notif_exists:
				Notification.objects.create(
					recipient=instance.teacher,
					title=title,
					message=message
				)
		except Exception:
			pass


@receiver(post_save, sender='courses.Enrollment')
def notify_enrollment_creation(sender, instance, created, **kwargs):
	if created:
		try:
			Notification.objects.create(
				recipient=instance.student,
				title="Course Enrollment",
				message=f"You have been enrolled in the course: {instance.course.name} ({instance.course.code}) for {instance.term}."
			)
		except Exception:
			pass


@receiver(post_save, sender='results.Result')
def notify_result_publication(sender, instance, created, **kwargs):
	if instance.published:
		try:
			title = "Result Published"
			message = f"Your result for {instance.course.name} ({instance.course.code}) has been published: Grade {instance.grade} (GPA: {instance.gpa})."
			notif_exists = Notification.objects.filter(
				recipient=instance.student,
				title=title,
				message__contains=instance.course.code
			).exists()
			if not notif_exists:
				Notification.objects.create(
					recipient=instance.student,
					title=title,
					message=message
				)
		except Exception:
			pass


@receiver(post_save, sender='timetable.TimetableEntry')
def notify_timetable_entry(sender, instance, created, **kwargs):
	if instance.published:
		try:
			title = "New Timetable Entry Published"
			message = f"A class session for {instance.course.name} ({instance.course.code}) has been scheduled on {instance.day.title()}s at {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')} in {instance.room}."
			
			if instance.course.teacher:
				Notification.objects.get_or_create(
					recipient=instance.course.teacher,
					title=title,
					message=message
				)
			
			from courses.models import Enrollment
			student_ids = Enrollment.objects.filter(course=instance.course).values_list('student_id', flat=True)
			notifications = [
				Notification(recipient_id=s_id, title=title, message=message)
				for s_id in student_ids
			]
			if notifications:
				Notification.objects.bulk_create(notifications)
		except Exception:
			pass


@receiver(post_save, sender='attendance.Attendance')
def notify_attendance_record(sender, instance, created, **kwargs):
	if not instance.is_draft:
		try:
			title = "Attendance Recorded"
			message = f"Your attendance for {instance.course.name} ({instance.course.code}) on {instance.date} has been recorded as: {instance.status.title()}."
			notif_exists = Notification.objects.filter(
				recipient=instance.student,
				title=title,
				message=message
			).exists()
			if not notif_exists:
				Notification.objects.create(
					recipient=instance.student,
					title=title,
					message=message
				)
		except Exception:
			pass


@receiver(post_save, sender='timetable.ExamSchedule')
def notify_exam_schedule(sender, instance, created, **kwargs):
	if instance.published:
		try:
			title = "Exam Scheduled"
			message = f"An exam for {instance.course.name} ({instance.course.code}) has been scheduled on {instance.date} at {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')} in {instance.room}."
			
			if instance.course.teacher:
				Notification.objects.get_or_create(
					recipient=instance.course.teacher,
					title=title,
					message=message
				)
			
			from courses.models import Enrollment
			student_ids = Enrollment.objects.filter(course=instance.course).values_list('student_id', flat=True)
			notifications = [
				Notification(recipient_id=s_id, title=title, message=message)
				for s_id in student_ids
			]
			if notifications:
				Notification.objects.bulk_create(notifications)
		except Exception:
			pass

