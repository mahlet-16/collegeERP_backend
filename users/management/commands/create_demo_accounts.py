from django.core.management.base import BaseCommand
from users.models import StudentProfile, TeacherProfile, User


class Command(BaseCommand):
    help = "Create standard demo users for the College ERP system."

    def handle(self, *args, **options):
        demo_users = [
            {
                "username": "admin",
                "password": "admin123",
                "first_name": "System",
                "last_name": "Administrator",
                "email": "admin@example.com",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "registrar",
                "password": "registrar123",
                "first_name": "Primary",
                "last_name": "Registrar",
                "email": "registrar@example.com",
                "role": User.Role.REGISTRAR,
            },
            {
                "username": "teacher",
                "password": "teacher123",
                "first_name": "Lead",
                "last_name": "Instructor",
                "email": "teacher@example.com",
                "role": User.Role.TEACHER,
            },
            {
                "username": "student",
                "password": "student123",
                "first_name": "Learner",
                "last_name": "Student",
                "email": "student@example.com",
                "role": User.Role.STUDENT,
            },
        ]

        for data in demo_users:
            defaults = {key: value for key, value in data.items() if key != "password"}
            user, created = User.objects.get_or_create(username=data["username"], defaults=defaults)
            if created:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created demo user '{user.username}'"))
            else:
                changed = False
                for field in ["first_name", "last_name", "email", "role"]:
                    if getattr(user, field) != data.get(field, getattr(user, field)):
                        setattr(user, field, data[field])
                        changed = True
                if not user.check_password(data["password"]):
                    user.set_password(data["password"])
                    changed = True
                if user.is_active is False:
                    user.is_active = True
                    changed = True
                if data.get("is_staff") and not user.is_staff:
                    user.is_staff = True
                    changed = True
                if data.get("is_superuser") and not user.is_superuser:
                    user.is_superuser = True
                    changed = True
                if changed:
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated demo user '{user.username}'"))
                else:
                    self.stdout.write(self.style.NOTICE(f"Demo user '{user.username}' already exists."))

            if user.role == User.Role.STUDENT:
                profile, _ = StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "student_id": "STU-DEMO-001",
                        "level": "Year 1",
                    },
                )
                if not profile.student_id:
                    profile.student_id = "STU-DEMO-001"
                    profile.level = profile.level or "Year 1"
                    profile.save(update_fields=["student_id", "level"])
            elif user.role == User.Role.TEACHER:
                profile, _ = TeacherProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "staff_id": "TCH-DEMO-001",
                        "office": "Academic Block",
                    },
                )
                if not profile.staff_id:
                    profile.staff_id = "TCH-DEMO-001"
                    profile.office = profile.office or "Academic Block"
                    profile.save(update_fields=["staff_id", "office"])
