from decimal import Decimal

from rest_framework import serializers

from courses.models import Enrollment, Section, Semester, AcademicYear
from users.models import StudentProfile
from .models import Result


class ResultSerializer(serializers.ModelSerializer):
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
        model = Result
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
            "mark",
            "grade",
            "gpa",
            "term",
            "is_draft",
            "entered_by",
            "published",
        ]
        read_only_fields = ["entered_by", "grade", "gpa"]

    @staticmethod
    def calculate_grade(mark):
        mark = Decimal(mark)
        if mark >= Decimal("90"):
            return "A+", Decimal("4.00")
        if mark >= Decimal("85"):
            return "A", Decimal("4.00")
        if mark >= Decimal("80"):
            return "A-", Decimal("3.75")
        if mark >= Decimal("75"):
            return "B+", Decimal("3.50")
        if mark >= Decimal("70"):
            return "B", Decimal("3.00")
        if mark >= Decimal("65"):
            return "C+", Decimal("2.50")
        if mark >= Decimal("60"):
            return "C", Decimal("2.00")
        if mark >= Decimal("50"):
            return "D", Decimal("1.00")
        return "F", Decimal("0.00")

    def validate_mark(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Mark must be between 0 and 100.")
        return value

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        if student and student.role != "student":
            raise serializers.ValidationError({"student": "Result user must be a student."})
        if student and course and not Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError("Student is not enrolled in this course.")
        if student and course and course.section_id:
            profile, _ = StudentProfile.objects.get_or_create(user=student)
            if profile.section_id != course.section_id:
                raise serializers.ValidationError("Results can only be entered for students in the course section.")

        request = self.context.get("request")
        if request and request.user.role == "teacher" and course and course.teacher_id != request.user.id:
            raise serializers.ValidationError("You can only enter results for your assigned courses.")
        published = attrs.get("published", getattr(self.instance, "published", False))
        is_draft = attrs.get("is_draft", getattr(self.instance, "is_draft", False))
        if request and request.user.role == "teacher" and published:
            raise serializers.ValidationError("Teachers cannot publish finalized results.")
        if published and is_draft:
            raise serializers.ValidationError("Draft results cannot be published.")

        if course:
            if not attrs.get("section") and course.section:
                attrs["section"] = course.section
            if not attrs.get("semester"):
                attrs["semester"] = course.semester or (course.section.semester if course.section else None)
            if not attrs.get("academic_year"):
                attrs["academic_year"] = getattr(attrs.get("semester"), "academic_year", None) or (course.section.academic_year if course.section else None)
            if not attrs.get("term"):
                ay_name = attrs["academic_year"].name if attrs.get("academic_year") else ""
                sem_name = attrs["semester"].name if attrs.get("semester") else ""
                attrs["term"] = f"{ay_name} {sem_name}".strip()

        return attrs

    def create(self, validated_data):
        validated_data["grade"], validated_data["gpa"] = self.calculate_grade(validated_data["mark"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "mark" in validated_data:
            validated_data["grade"], validated_data["gpa"] = self.calculate_grade(validated_data["mark"])
        return super().update(instance, validated_data)
