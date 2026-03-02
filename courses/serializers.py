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

    class Meta:
        model = Course
        fields = ["id", "code", "name", "credit_hour", "teacher", "teacher_name"]

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() or obj.teacher.username


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "course", "course_code", "term"]
