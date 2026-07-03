from rest_framework import serializers

from courses.models import Enrollment
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
            "is_draft",
            "recorded_by",
        ]
        read_only_fields = ["recorded_by"]

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        if student and student.role != "student":
            raise serializers.ValidationError({"student": "Attendance user must be a student."})
        if student and course and not Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError("Student is not enrolled in this course.")

        request = self.context.get("request")
        if request and request.user.role == "teacher" and course and course.teacher_id != request.user.id:
            raise serializers.ValidationError("You can only record attendance for your assigned courses.")
        return attrs
