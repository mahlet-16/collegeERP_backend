import csv
import io

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from users.models import AuditLog, User
from users.permissions import IsAdminOrRegistrar

from .models import AcademicYear, Classroom, College, Course, Department, Enrollment, Program, Section, Semester
from .serializers import (
	AcademicYearSerializer,
	ClassroomSerializer,
	CollegeSerializer,
	CourseSerializer,
	DepartmentSerializer,
	EnrollmentSerializer,
	ProgramSerializer,
	SectionSerializer,
	SemesterSerializer,
)


def write_audit(request, action, instance, detail=None):
	safe_detail = {}
	for key, value in (detail or {}).items():
		if hasattr(value, "pk"):
			safe_detail[key] = value.pk
		else:
			safe_detail[key] = value
	AuditLog.objects.create(
		actor=request.user if request.user and request.user.is_authenticated else None,
		action=action,
		model_name=instance.__class__.__name__,
		object_id=str(instance.pk),
		detail=safe_detail,
	)


class CollegeViewSet(viewsets.ModelViewSet):
	queryset = College.objects.all().order_by("name")
	serializer_class = CollegeSerializer
	search_fields = ["name", "code", "address"]
	ordering_fields = ["name", "code"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "college.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "college.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "college.deleted", instance)
		instance.delete()


class DepartmentViewSet(viewsets.ModelViewSet):
	queryset = Department.objects.select_related("college").all().order_by("name")
	serializer_class = DepartmentSerializer
	filterset_fields = ["college"]
	search_fields = ["name", "college__name"]
	ordering_fields = ["name", "college__name"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "department.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "department.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "department.deleted", instance)
		instance.delete()


class ProgramViewSet(viewsets.ModelViewSet):
	queryset = Program.objects.select_related("department").all().order_by("name")
	serializer_class = ProgramSerializer
	filterset_fields = ["department"]
	search_fields = ["name", "department__name"]
	ordering_fields = ["name", "department__name"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "program.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "program.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "program.deleted", instance)
		instance.delete()


class AcademicYearViewSet(viewsets.ModelViewSet):
	queryset = AcademicYear.objects.all().order_by("-is_active", "name")
	serializer_class = AcademicYearSerializer
	filterset_fields = ["is_active"]
	search_fields = ["name"]
	ordering_fields = ["name", "start_date", "end_date", "is_active"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "academic_year.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "academic_year.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "academic_year.deleted", instance)
		instance.delete()


class SemesterViewSet(viewsets.ModelViewSet):
	queryset = Semester.objects.select_related("academic_year").all().order_by("academic_year__name", "number")
	serializer_class = SemesterSerializer
	filterset_fields = ["academic_year", "is_active", "number"]
	search_fields = ["name", "academic_year__name"]
	ordering_fields = ["academic_year__name", "number", "name", "is_active"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "semester.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "semester.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "semester.deleted", instance)
		instance.delete()


class SectionViewSet(viewsets.ModelViewSet):
	serializer_class = SectionSerializer
	filterset_fields = ["program", "academic_year", "semester", "year_level", "is_active"]
	search_fields = ["name", "program__name", "program__department__name", "semester__name", "academic_year__name"]
	ordering_fields = ["program__name", "year_level", "name", "capacity", "is_active"]

	def get_queryset(self):
		queryset = (
			Section.objects.select_related("program", "program__department", "academic_year", "semester")
			.annotate(student_count=Count("students", distinct=True), course_count=Count("courses", distinct=True))
			.order_by("program__name", "year_level", "name")
		)
		user = self.request.user
		if user.role == User.Role.STUDENT:
			section_id = getattr(getattr(user, "student_profile", None), "section_id", None)
			return queryset.filter(id=section_id) if section_id else queryset.none()
		if user.role == User.Role.TEACHER:
			return queryset.filter(courses__teacher=user).distinct()
		return queryset

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "section.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "section.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "section.deleted", instance)
		instance.delete()


class ClassroomViewSet(viewsets.ModelViewSet):
	queryset = Classroom.objects.select_related("department").all().order_by("building", "name")
	serializer_class = ClassroomSerializer
	filterset_fields = ["department", "is_active"]
	search_fields = ["name", "building", "department__name"]
	ordering_fields = ["name", "building", "capacity", "is_active"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "classroom.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "classroom.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "classroom.deleted", instance)
		instance.delete()


class CourseViewSet(viewsets.ModelViewSet):
	queryset = Course.objects.select_related("teacher", "program", "program__department", "section", "semester").all().order_by("code")
	serializer_class = CourseSerializer
	filterset_fields = ["teacher", "program", "section", "semester"]
	search_fields = ["code", "name", "teacher__username", "program__name", "section__name", "semester__name"]
	ordering_fields = ["code", "name", "credit_hour", "program__name", "section__name", "teacher__username"]

	def get_queryset(self):
		queryset = super().get_queryset()
		user = self.request.user
		if user.role == User.Role.STUDENT:
			section_id = getattr(getattr(user, "student_profile", None), "section_id", None)
			if section_id:
				return queryset.filter(section_id=section_id).distinct()
			return queryset.filter(enrollments__student=user).distinct()
		if user.role == User.Role.TEACHER:
			return queryset.filter(teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "course.created", instance, serializer.validated_data)

	def perform_update(self, serializer):
		instance = serializer.save()
		write_audit(self.request, "course.updated", instance, serializer.validated_data)

	def perform_destroy(self, instance):
		write_audit(self.request, "course.deleted", instance)
		instance.delete()


class EnrollmentViewSet(viewsets.ModelViewSet):
	queryset = Enrollment.objects.select_related("student", "course", "course__section").all().order_by("term")
	serializer_class = EnrollmentSerializer
	filterset_fields = ["student", "course", "term"]
	search_fields = ["student__username", "course__code", "course__name", "course__section__name", "term"]
	ordering_fields = ["term", "student__username", "course__code", "course__section__name"]

	def get_queryset(self):
		queryset = super().get_queryset()
		user = self.request.user
		section_id = self.request.query_params.get("section")
		if section_id:
			queryset = queryset.filter(course__section_id=section_id)
		if user.role == "student":
			return queryset.filter(student=user)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]

	def perform_create(self, serializer):
		enrollment = serializer.save()
		write_audit(
			self.request,
			"enrollment.created",
			enrollment,
			{"student": enrollment.student_id, "course": enrollment.course_id, "term": enrollment.term},
		)

	def perform_update(self, serializer):
		enrollment = serializer.save()
		write_audit(
			self.request,
			"enrollment.updated",
			enrollment,
			{"student": enrollment.student_id, "course": enrollment.course_id, "term": enrollment.term},
		)

	def perform_destroy(self, instance):
		write_audit(
			self.request,
			"enrollment.deleted",
			instance,
			{"student": instance.student_id, "course": instance.course_id, "term": instance.term},
		)
		instance.delete()

	@action(detail=False, methods=["post"], parser_classes=[MultiPartParser], permission_classes=[IsAdminOrRegistrar])
	def bulk_upload(self, request):
		upload = request.FILES.get("file")
		if not upload:
			return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

		reader = csv.DictReader(io.StringIO(upload.read().decode("utf-8-sig")))
		created = []
		errors = []
		for index, row in enumerate(reader, start=2):
			try:
				student = User.objects.get(username=row.get("student", "").strip(), role=User.Role.STUDENT)
				course = Course.objects.get(code=row.get("course", "").strip())
			except (User.DoesNotExist, Course.DoesNotExist) as exc:
				errors.append({"row": index, "detail": str(exc)})
				continue

			serializer = self.get_serializer(
				data={"student": student.id, "course": course.id, "term": row.get("term", "").strip()}
			)
			if serializer.is_valid():
				created.append(serializer.save())
			else:
				errors.append({"row": index, "detail": serializer.errors})

		return Response(
			{"created": EnrollmentSerializer(created, many=True).data, "errors": errors},
			status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
		)
