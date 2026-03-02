from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsTeacher

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
	queryset = Attendance.objects.select_related("student", "course", "recorded_by").all()
	serializer_class = AttendanceSerializer

	def get_queryset(self):
		queryset = super().get_queryset().order_by("-date")
		user = self.request.user
		if user.role == "student":
			return queryset.filter(student=user)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsTeacher()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		serializer.save(recorded_by=self.request.user)
