from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_code",
            "date",
            "status",
            "comment",
            "recorded_by",
        ]
        read_only_fields = ["recorded_by"]
