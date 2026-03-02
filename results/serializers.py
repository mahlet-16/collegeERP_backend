from rest_framework import serializers

from .models import Result


class ResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Result
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_code",
            "mark",
            "grade",
            "gpa",
            "term",
            "entered_by",
            "published",
        ]
        read_only_fields = ["entered_by"]
