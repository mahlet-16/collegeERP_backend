from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from users.models import StudentProfile, TeacherProfile
from courses.models import Course, Program, Department, AcademicYear, Semester, Section, Classroom
from results.models import Result
from results.serializers import ResultSerializer
from timetable.models import TimetableEntry
from timetable.serializers import TimetableEntrySerializer

User = get_user_model()

class CollegeERPTestCase(TestCase):
    def setUp(self):
        # Setup basic academic structure using get_or_create because migrations pre-seed data
        self.dept, _ = Department.objects.get_or_create(name="Computer Science")
        self.program, _ = Program.objects.get_or_create(name="Software Engineering", department=self.dept)
        self.year, _ = AcademicYear.objects.get_or_create(name="2025/2026", defaults={"is_active": True})
        self.semester, _ = Semester.objects.get_or_create(
            name="Semester 1",
            academic_year=self.year,
            defaults={"number": 1, "is_active": True}
        )
        self.section, _ = Section.objects.get_or_create(
            name="Section A",
            program=self.program,
            academic_year=self.year,
            semester=self.semester,
            defaults={"year_level": 1, "capacity": 30}
        )
        self.classroom, _ = Classroom.objects.get_or_create(name="Lab 1", defaults={"capacity": 30, "department": self.dept})

    def test_user_profile_sync_student(self):
        """Creating a student user must automatically create a StudentProfile and not a TeacherProfile."""
        student_user = User.objects.create_user(
            username="stu.test",
            password="testpassword123",
            role=User.Role.STUDENT
        )
        self.assertTrue(StudentProfile.objects.filter(user=student_user).exists())
        self.assertFalse(TeacherProfile.objects.filter(user=student_user).exists())
        
        # Test updating role to teacher deletes student profile and creates teacher profile
        student_user.role = User.Role.TEACHER
        student_user.save()
        self.assertFalse(StudentProfile.objects.filter(user=student_user).exists())
        self.assertTrue(TeacherProfile.objects.filter(user=student_user).exists())

    def test_user_profile_sync_teacher(self):
        """Creating a teacher user must automatically create a TeacherProfile and not a StudentProfile."""
        teacher_user = User.objects.create_user(
            username="tch.test",
            password="testpassword123",
            role=User.Role.TEACHER
        )
        self.assertFalse(StudentProfile.objects.filter(user=teacher_user).exists())
        self.assertTrue(TeacherProfile.objects.filter(user=teacher_user).exists())

    def test_grade_calculation(self):
        """Verify grade letters and GPA points correspond to numeric marks."""
        grade_a_plus, gpa_a_plus = ResultSerializer.calculate_grade(95)
        self.assertEqual(grade_a_plus, "A+")
        self.assertEqual(gpa_a_plus, Decimal("4.00"))

        grade_b_plus, gpa_b_plus = ResultSerializer.calculate_grade(76)
        self.assertEqual(grade_b_plus, "B+")
        self.assertEqual(gpa_b_plus, Decimal("3.50"))

        grade_f, gpa_f = ResultSerializer.calculate_grade(42)
        self.assertEqual(grade_f, "F")
        self.assertEqual(gpa_f, Decimal("0.00"))

    def test_timetable_conflict_validation(self):
        """Timetable entries must check for room and teacher conflicts."""
        teacher1 = User.objects.create_user(username="teacher1", password="password", role=User.Role.TEACHER)
        teacher2 = User.objects.create_user(username="teacher2", password="password", role=User.Role.TEACHER)
        
        course1 = Course.objects.create(
            code="CS101",
            name="Intro to CS",
            program=self.program,
            section=self.section,
            semester=self.semester,
            teacher=teacher1
        )
        course2 = Course.objects.create(
            code="CS102",
            name="OOP",
            program=self.program,
            section=self.section,
            semester=self.semester,
            teacher=teacher2
        )

        # Create entry 1
        entry1 = TimetableEntry.objects.create(
            term="2025/2026 Semester 1",
            day=TimetableEntry.Day.MONDAY,
            start_time="09:00:00",
            end_time="10:30:00",
            room="Lab 1",
            classroom=self.classroom,
            course=course1,
            section=self.section
        )

        # Create overlapping entry with same room (Lab 1) using serializer to test validation
        serializer = TimetableEntrySerializer(data={
            "term": "2025/2026 Semester 1",
            "day": TimetableEntry.Day.MONDAY,
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "room": "Lab 1",
            "classroom": self.classroom.id,
            "course": course2.id,
            "section": self.section.id
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertTrue(any("conflict" in str(err).lower() for err in serializer.errors["non_field_errors"]))

    def test_bulk_create_users_resolution(self):
        """Test bulk user creation resolves names and roles case-insensitively."""
        registrar = User.objects.create_user(username="registrar_test", password="password", role=User.Role.REGISTRAR)
        csv_content = (
            "username,password,role,first_name,last_name,email,program,section\n"
            "csvstudent,College@pass12349,Student,Csv,Student,csv@test.com,Software Engineering,Section A\n"
        )
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_file = SimpleUploadedFile("users.csv", csv_content.encode("utf-8"), content_type="text/csv")
        from django.urls import reverse
        from rest_framework.test import APIClient
        
        client = APIClient()
        client.force_authenticate(user=registrar)
        url = reverse("user-bulk-create")
        response = client.post(url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["created"]), 1)
        
        student_user = User.objects.get(username="csvstudent")
        self.assertEqual(student_user.role, User.Role.STUDENT)
        self.assertEqual(student_user.student_profile.program, self.program)
        self.assertEqual(student_user.student_profile.section, self.section)

