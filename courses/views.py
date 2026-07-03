import csv
import io

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from users.models import AuditLog, User
from users.permissions import IsAdminOrRegistrar, IsRegistrar

from .models import Course, Department, Enrollment, Program
from .serializers import (
	CourseSerializer,
	DepartmentSerializer,
	EnrollmentSerializer,
	ProgramSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
	queryset = Department.objects.all().order_by("name")
	serializer_class = DepartmentSerializer
	search_fields = ["name"]
	ordering_fields = ["name"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsRegistrar()]


class ProgramViewSet(viewsets.ModelViewSet):
	queryset = Program.objects.select_related("department").all().order_by("name")
	serializer_class = ProgramSerializer
	filterset_fields = ["department"]
	search_fields = ["name", "department__name"]
	ordering_fields = ["name", "department__name"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsRegistrar()]


class CourseViewSet(viewsets.ModelViewSet):
	queryset = Course.objects.select_related("teacher", "program").all().order_by("code")
	serializer_class = CourseSerializer
	filterset_fields = ["teacher", "program"]
	search_fields = ["code", "name", "teacher__username", "program__name"]
	ordering_fields = ["code", "name", "credit_hour", "program__name", "teacher__username"]

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsRegistrar()]


class EnrollmentViewSet(viewsets.ModelViewSet):
	queryset = Enrollment.objects.select_related("student", "course").all().order_by("term")
	serializer_class = EnrollmentSerializer
	filterset_fields = ["student", "course", "term"]
	search_fields = ["student__username", "course__code", "course__name", "term"]
	ordering_fields = ["term", "student__username", "course__code"]

	def get_queryset(self):
		queryset = super().get_queryset()
		user = self.request.user
		if user.role == "student":
			return queryset.filter(student=user)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsRegistrar()]

	def perform_create(self, serializer):
		enrollment = serializer.save()
		AuditLog.objects.create(
			actor=self.request.user,
			action="enrollment.created",
			model_name="Enrollment",
			object_id=str(enrollment.pk),
			detail={"student": enrollment.student_id, "course": enrollment.course_id, "term": enrollment.term},
		)

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
