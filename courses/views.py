from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdminOrRegistrar

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

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]


class ProgramViewSet(viewsets.ModelViewSet):
	queryset = Program.objects.select_related("department").all().order_by("name")
	serializer_class = ProgramSerializer

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]


class CourseViewSet(viewsets.ModelViewSet):
	queryset = Course.objects.select_related("teacher").all().order_by("code")
	serializer_class = CourseSerializer

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [IsAuthenticated()]
		return [IsAdminOrRegistrar()]


class EnrollmentViewSet(viewsets.ModelViewSet):
	queryset = Enrollment.objects.select_related("student", "course").all().order_by("term")
	serializer_class = EnrollmentSerializer

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
		return [IsAdminOrRegistrar()]
