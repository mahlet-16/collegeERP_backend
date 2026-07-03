from rest_framework import serializers

from .models import Course, Department, Enrollment, Program


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    program_name = serializers.CharField(source="program.name", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "name", "credit_hour", "program", "program_name", "teacher", "teacher_name"]

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() or obj.teacher.username

    def validate_teacher(self, value):
        if value and value.role != "teacher":
            raise serializers.ValidationError("Assigned user must be a teacher.")
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "course", "course_code", "term"]

    def validate_student(self, value):
        if value.role != "student":
            raise serializers.ValidationError("Enrolled user must be a student.")
        return value
