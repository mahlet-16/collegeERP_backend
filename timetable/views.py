from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdminOrRegistrar

from .models import TimetableEntry
from .serializers import TimetableEntrySerializer


class TimetableEntryViewSet(viewsets.ModelViewSet):
	queryset = TimetableEntry.objects.select_related("course", "assigned_by", "course__teacher").all()
	serializer_class = TimetableEntrySerializer

	def get_queryset(self):
		queryset = super().get_queryset().order_by("day", "start_time")
		user = self.request.user
		if user.role == "student":
			return queryset.filter(published=True)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user, published=True)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsAdminOrRegistrar()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		serializer.save(assigned_by=self.request.user)
