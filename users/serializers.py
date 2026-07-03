from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from courses.models import Department, Program
from .models import AuditLog, Notification, StudentProfile, SystemSetting, TeacherProfile, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "phone", "is_active"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(), required=False, allow_null=True, write_only=True
    )
    student_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    level = serializers.CharField(required=False, allow_blank=True, write_only=True)
    address = serializers.CharField(required=False, allow_blank=True, write_only=True)
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
            "student_id",
            "level",
            "address",
            "department",
            "staff_id",
            "office",
        ]

    def validate_password(self, value):
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

    @staticmethod
    def _generated_profile_id(prefix, model, field_name, user_id):
        candidate = f"{prefix}-{user_id:05d}"
        suffix = 1
        while model.objects.filter(**{field_name: candidate}).exists():
            suffix += 1
            candidate = f"{prefix}-{user_id:05d}-{suffix}"
        return candidate

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
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == User.Role.STUDENT:
            if not student_profile["student_id"]:
                student_profile["student_id"] = self._generated_profile_id(
                    "STU", StudentProfile, "student_id", user.id
                )
            StudentProfile.objects.update_or_create(user=user, defaults=student_profile)
        elif user.role == User.Role.TEACHER:
            if not teacher_profile["staff_id"]:
                teacher_profile["staff_id"] = self._generated_profile_id(
                    "TCH", TeacherProfile, "staff_id", user.id
                )
            TeacherProfile.objects.update_or_create(user=user, defaults=teacher_profile)
        return user


class UserManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "phone", "is_active"]


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = StudentProfile
        fields = ["id", "user", "username", "program", "student_id", "level", "address"]
        read_only_fields = ["user"]


class TeacherProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ["id", "user", "username", "staff_id", "department", "office"]
        read_only_fields = ["user"]


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
