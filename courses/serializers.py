from rest_framework import serializers

from users.models import StudentProfile

from .models import (
    AcademicYear,
    Classroom,
    College,
    Course,
    Department,
    Enrollment,
    Program,
    Section,
    Semester,
)


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "college", "college_name"]


class ProgramSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    college_name = serializers.CharField(source="department.college.name", read_only=True)

    class Meta:
        model = Program
        fields = ["id", "name", "department", "department_name", "college_name"]


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"


class SemesterSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = Semester
        fields = ["id", "name", "academic_year", "academic_year_name", "number", "is_active"]


class SectionSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source="program.name", read_only=True)
    department_name = serializers.CharField(source="program.department.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)
    label = serializers.CharField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    course_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Section
        fields = [
            "id",
            "name",
            "program",
            "program_name",
            "department_name",
            "academic_year",
            "academic_year_name",
            "semester",
            "semester_name",
            "year_level",
            "capacity",
            "is_active",
            "label",
            "student_count",
            "course_count",
        ]

    def validate(self, attrs):
        semester = attrs.get("semester", getattr(self.instance, "semester", None))
        academic_year = attrs.get("academic_year", getattr(self.instance, "academic_year", None))
        if semester and academic_year and semester.academic_year_id != academic_year.id:
            raise serializers.ValidationError("Semester must belong to the selected academic year.")
        if semester and not academic_year:
            attrs["academic_year"] = semester.academic_year
        return attrs


class ClassroomSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Classroom
        fields = ["id", "name", "building", "capacity", "department", "department_name", "is_active"]


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    program_name = serializers.CharField(source="program.name", read_only=True)
    section_name = serializers.CharField(source="section.label", read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)
    department_name = serializers.CharField(source="program.department.name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "code",
            "name",
            "credit_hour",
            "program",
            "program_name",
            "section",
            "section_name",
            "semester",
            "semester_name",
            "department_name",
            "teacher",
            "teacher_name",
        ]

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() or obj.teacher.username

    def validate_teacher(self, value):
        if value and value.role != "teacher":
            raise serializers.ValidationError("Assigned user must be a teacher.")
        return value

    def validate(self, attrs):
        section = attrs.get("section", getattr(self.instance, "section", None))
        program = attrs.get("program", getattr(self.instance, "program", None))
        semester = attrs.get("semester", getattr(self.instance, "semester", None))

        if section:
            if program and section.program_id != program.id:
                raise serializers.ValidationError("Course program must match the selected section program.")
            attrs["program"] = section.program
            if section.semester and not semester:
                attrs["semester"] = section.semester
        elif not self.instance:
            raise serializers.ValidationError({"section": "Course must belong to a section."})
        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    section = serializers.IntegerField(source="course.section_id", read_only=True)
    section_name = serializers.CharField(source="course.section.label", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_code",
            "course_name",
            "section",
            "section_name",
            "term",
        ]

    def get_student_name(self, obj):
        full_name = f"{obj.student.first_name} {obj.student.last_name}".strip()
        return full_name or obj.student.username

    def validate_student(self, value):
        if value.role != "student":
            raise serializers.ValidationError("Enrolled user must be a student.")
        return value

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        if not student or not course:
            return attrs

        profile, _ = StudentProfile.objects.get_or_create(user=student)
        if course.section_id is None:
            raise serializers.ValidationError("Course must belong to a section before enrollment.")
        if profile.section_id and profile.section_id != course.section_id:
            raise serializers.ValidationError("Student can only be enrolled in courses from their assigned section.")
        section = course.section
        if section and section.capacity:
            assigned = StudentProfile.objects.filter(section=section).count()
            if not profile.section_id and assigned >= section.capacity:
                raise serializers.ValidationError(f"Section '{section.label}' has reached its capacity of {section.capacity}.")
        return attrs

    def create(self, validated_data):
        enrollment = super().create(validated_data)
        profile, _ = StudentProfile.objects.get_or_create(user=enrollment.student)
        if enrollment.course.section_id and not profile.section_id:
            profile.section = enrollment.course.section
            profile.program = enrollment.course.program
            profile.level = f"Year {enrollment.course.section.year_level}"
            profile.save(update_fields=["section", "program", "level"])
        return enrollment
