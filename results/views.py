from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsTeacher

from .models import Result
from .serializers import ResultSerializer


class ResultViewSet(viewsets.ModelViewSet):
	queryset = Result.objects.select_related("student", "course", "entered_by").all()
	serializer_class = ResultSerializer

	def get_queryset(self):
		queryset = super().get_queryset().order_by("course__code")
		user = self.request.user
		if user.role == "student":
			return queryset.filter(student=user, published=True)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsTeacher()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		serializer.save(entered_by=self.request.user)
