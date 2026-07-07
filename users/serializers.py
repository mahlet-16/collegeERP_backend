import secrets
import string

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from courses.models import Department, Program, Section, get_default_section
from .models import AuditLog, Notification, StudentProfile, SystemSetting, TeacherProfile, User, generated_profile_id


def generate_password():
    alphabet = string.ascii_letters + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"College@{suffix}9"


def generate_username(role, first_name="", last_name=""):
    base_parts = [first_name, last_name]
    base = ".".join(part.strip().lower() for part in base_parts if part and part.strip())
    if not base:
        base = role or "user"
    base = "".join(char if char.isalnum() or char in "._-" else "." for char in base).strip(".")
    candidate = base[:135] or role or "user"
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f"{base[:126]}{suffix}"
    return candidate


class UserSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="student_profile.student_id", read_only=True)
    staff_id = serializers.CharField(source="teacher_profile.staff_id", read_only=True)
    program_name = serializers.CharField(source="student_profile.program.name", read_only=True)
    section = serializers.IntegerField(source="student_profile.section_id", read_only=True)
    section_name = serializers.CharField(source="student_profile.section.label", read_only=True)
    semester_name = serializers.CharField(source="student_profile.section.semester.name", read_only=True)
    year_level = serializers.IntegerField(source="student_profile.section.year_level", read_only=True)
    department_name = serializers.CharField(source="teacher_profile.department.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "is_active",
            "student_id",
            "staff_id",
            "program_name",
            "section",
            "section_name",
            "semester_name",
            "year_level",
            "department_name",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(), required=False, allow_null=True, write_only=True
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), required=False, allow_null=True, write_only=True
    )
    student_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    level = serializers.CharField(required=False, allow_blank=True, write_only=True)
    address = serializers.CharField(required=False, allow_blank=True, write_only=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True, write_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True, write_only=True
    )
    staff_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    office = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "program",
            "section",
            "student_id",
            "level",
            "address",
            "avatar_url",
            "department",
            "staff_id",
            "office",
        ]

    def validate_password(self, value):
        if not value:
            return value
        validate_password(value)
        return value

    def validate_student_id(self, value):
        if value and StudentProfile.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("Student ID already exists.")
        return value

    def validate_staff_id(self, value):
        if value and TeacherProfile.objects.filter(staff_id=value).exists():
            raise serializers.ValidationError("Staff ID already exists.")
        return value

    def create(self, validated_data):
        student_profile = {
            "program": validated_data.pop("program", None),
            "student_id": validated_data.pop("student_id", None),
            "level": validated_data.pop("level", ""),
            "address": validated_data.pop("address", ""),
        }
        teacher_profile = {
            "department": validated_data.pop("department", None),
            "staff_id": validated_data.pop("staff_id", None),
            "office": validated_data.pop("office", ""),
        }
        student_profile["section"] = validated_data.pop("section", None)
        student_profile["avatar_url"] = validated_data.pop("avatar_url", "")
        requested_password = validated_data.pop("password", "")
        if not validated_data.get("username"):
            validated_data["username"] = generate_username(
                validated_data.get("role", User.Role.STUDENT),
                validated_data.get("first_name", ""),
                validated_data.get("last_name", ""),
            )
            self.generated_username = validated_data["username"]
        password = requested_password or generate_password()
        self.generated_password = password if not requested_password else None
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == User.Role.STUDENT:
            if not student_profile["section"]:
                try:
                    student_profile["section"] = get_default_section()
                except Exception:
                    student_profile["section"] = None
            if not student_profile["program"] and student_profile["section"]:
                student_profile["program"] = student_profile["section"].program
            if not student_profile["level"] and student_profile["section"]:
                student_profile["level"] = f"Year {student_profile['section'].year_level}"
            if not student_profile["student_id"]:
                existing_profile = getattr(user, "student_profile", None)
                student_profile["student_id"] = getattr(existing_profile, "student_id", None) or generated_profile_id(
                    "STU", StudentProfile, "student_id", user.id
                )
            StudentProfile.objects.update_or_create(user=user, defaults=student_profile)
        elif user.role == User.Role.TEACHER:
            if not teacher_profile["staff_id"]:
                existing_profile = getattr(user, "teacher_profile", None)
                teacher_profile["staff_id"] = getattr(existing_profile, "staff_id", None) or generated_profile_id(
                    "TCH", TeacherProfile, "staff_id", user.id
                )
            TeacherProfile.objects.update_or_create(user=user, defaults=teacher_profile)
        return user


class UserManageSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), required=False, allow_null=True
    )
    program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(), required=False, allow_null=True
    )
    level = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    staff_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True
    )
    office = serializers.CharField(required=False, allow_blank=True)

    section_name = serializers.CharField(source="student_profile.section.label", read_only=True)
    program_name = serializers.CharField(source="student_profile.program.name", read_only=True)
    department_name = serializers.CharField(source="teacher_profile.department.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "is_active",
            "student_id",
            "section",
            "section_name",
            "program",
            "program_name",
            "level",
            "address",
            "staff_id",
            "department",
            "department_name",
            "office",
        ]

    def update(self, instance, validated_data):
        student_profile_data = {
            "student_id": validated_data.pop("student_id", None),
            "section": validated_data.pop("section", None),
            "program": validated_data.pop("program", None),
            "level": validated_data.pop("level", None),
            "address": validated_data.pop("address", None),
        }
        teacher_profile_data = {
            "staff_id": validated_data.pop("staff_id", None),
            "department": validated_data.pop("department", None),
            "office": validated_data.pop("office", None),
        }

        user = super().update(instance, validated_data)

        from .models import sync_user_role_profile
        sync_user_role_profile(user)

        if user.role == User.Role.STUDENT:
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            for field, val in student_profile_data.items():
                if val is not None:
                    setattr(profile, field, val)
            if profile.section and (student_profile_data["section"] is not None and student_profile_data["program"] is None):
                profile.program = profile.section.program
            profile.save()

        elif user.role == User.Role.TEACHER:
            profile, _ = TeacherProfile.objects.get_or_create(user=user)
            for field, val in teacher_profile_data.items():
                if val is not None:
                    setattr(profile, field, val)
            profile.save()

        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.role == User.Role.STUDENT:
            profile = getattr(instance, "student_profile", None)
            if profile:
                ret["student_id"] = profile.student_id
                ret["section"] = profile.section.id if profile.section else None
                ret["program"] = profile.program.id if profile.program else None
                ret["level"] = profile.level
                ret["address"] = profile.address
        elif instance.role == User.Role.TEACHER:
            profile = getattr(instance, "teacher_profile", None)
            if profile:
                ret["staff_id"] = profile.staff_id
                ret["department"] = profile.department.id if profile.department else None
                ret["office"] = profile.office
        return ret


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", required=False, allow_blank=True)
    phone = serializers.CharField(source="user.phone", required=False, allow_blank=True)
    program_name = serializers.CharField(source="program.name", read_only=True)
    department_name = serializers.CharField(source="program.department.name", read_only=True)
    section_name = serializers.CharField(source="section.label", read_only=True)
    semester_name = serializers.CharField(source="section.semester.name", read_only=True)
    academic_year_name = serializers.CharField(source="section.academic_year.name", read_only=True)
    year_level = serializers.IntegerField(source="section.year_level", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "program",
            "program_name",
            "department_name",
            "section",
            "section_name",
            "semester_name",
            "academic_year_name",
            "year_level",
            "student_id",
            "level",
            "address",
            "emergency_contact",
            "avatar_url",
        ]
        read_only_fields = ["user"]

    def validate_student_id(self, value):
        if value and StudentProfile.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(student_id=value).exists():
            raise serializers.ValidationError("Student ID already exists.")
        return value

    def validate(self, attrs):
        section = attrs.get("section", getattr(self.instance, "section", None))
        if section:
            attrs["program"] = section.program
        request = self.context.get("request")
        if request and request.user.role == User.Role.STUDENT:
            protected = {"program", "section", "student_id", "level"}
            if protected.intersection(attrs.keys()):
                raise serializers.ValidationError("Academic placement is managed by the registrar.")
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        if user_data:
            instance.user.save(update_fields=list(user_data.keys()))
        return super().update(instance, validated_data)


class TeacherProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ["id", "user", "username", "staff_id", "department", "department_name", "office"]
        read_only_fields = ["user"]

    def validate_staff_id(self, value):
        if value and TeacherProfile.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(staff_id=value).exists():
            raise serializers.ValidationError("Staff ID already exists.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "recipient", "title", "message", "read", "created_at"]
        read_only_fields = ["created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_name", "action", "model_name", "object_id", "detail", "created_at"]
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)

    class Meta:
        model = SystemSetting
        fields = ["id", "key", "value", "updated_by", "updated_by_name", "updated_at"]
        read_only_fields = ["updated_by", "updated_at"]
