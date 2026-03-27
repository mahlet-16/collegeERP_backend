from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

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
			return [IsAuthenticated()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		if self.request.user.role != "teacher":
			raise PermissionDenied("Only teachers can enter results.")
		serializer.save(entered_by=self.request.user)

	def perform_update(self, serializer):
		user = self.request.user
		instance = self.get_object()

		# Teachers can update academic fields on their assigned courses but cannot publish.
		if user.role == "teacher":
			if instance.course.teacher_id != user.id:
				raise PermissionDenied("You can only update results for your assigned courses.")
			if serializer.validated_data.get("published") is True:
				raise PermissionDenied("Teachers cannot publish finalized results.")
			serializer.save(entered_by=user)
			return

		# Registrar/Admin may only toggle publishing state for validation/finalization.
		if user.role in ["registrar", "admin"]:
			allowed_fields = {"published"}
			provided_fields = set(serializer.validated_data.keys())
			if not provided_fields.issubset(allowed_fields):
				raise PermissionDenied("Registrar/Admin can only publish or unpublish results.")
			serializer.save()
			return

		raise PermissionDenied("Not allowed to update results.")

	def perform_destroy(self, instance):
		user = self.request.user
		if user.role not in ["teacher", "admin"]:
			raise PermissionDenied("Only teacher or admin can delete results.")
		if user.role == "teacher" and instance.course.teacher_id != user.id:
			raise PermissionDenied("You can only delete results for your assigned courses.")
		instance.delete()
