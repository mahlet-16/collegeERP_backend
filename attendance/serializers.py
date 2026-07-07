from rest_framework import serializers

from courses.models import Enrollment, Section, Semester, AcademicYear
from users.models import StudentProfile
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), required=False, allow_null=True
    )
    semester = serializers.PrimaryKeyRelatedField(
        queryset=Semester.objects.all(), required=False, allow_null=True
    )
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), required=False, allow_null=True
    )
    section_name = serializers.CharField(source="section.label", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_code",
            "course_name",
            "section",
            "section_name",
            "semester",
            "academic_year",
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
        if student and course and course.section_id:
            profile, _ = StudentProfile.objects.get_or_create(user=student)
            if profile.section_id != course.section_id:
                raise serializers.ValidationError("Attendance can only be recorded for students in the course section.")

        request = self.context.get("request")
        if request and request.user.role == "teacher" and course and course.teacher_id != request.user.id:
            raise serializers.ValidationError("You can only record attendance for your assigned courses.")

        if course:
            if not attrs.get("section") and course.section:
                attrs["section"] = course.section
            if not attrs.get("semester"):
                attrs["semester"] = course.semester or (course.section.semester if course.section else None)
            if not attrs.get("academic_year"):
                attrs["academic_year"] = getattr(attrs.get("semester"), "academic_year", None) or (course.section.academic_year if course.section else None)

        return attrs
