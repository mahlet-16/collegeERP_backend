from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import AuditLog
from .models import Result
from .serializers import ResultSerializer


class ResultViewSet(viewsets.ModelViewSet):
	queryset = Result.objects.select_related("student", "course", "entered_by").all()
	serializer_class = ResultSerializer
	filterset_fields = ["student", "course", "term", "published", "is_draft"]
	search_fields = ["student__username", "course__code", "course__name", "term", "grade"]
	ordering_fields = ["term", "mark", "gpa", "grade", "published", "course__code", "student__username"]

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
		result = serializer.save(entered_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="result.created",
			model_name="Result",
			object_id=str(result.pk),
			detail={"course": result.course_id, "student": result.student_id, "draft": result.is_draft},
		)

	def perform_update(self, serializer):
		user = self.request.user
		instance = self.get_object()

		# Teachers can update academic fields on their assigned courses but cannot publish.
		if user.role == "teacher":
			if instance.course.teacher_id != user.id:
				raise PermissionDenied("You can only update results for your assigned courses.")
			if serializer.validated_data.get("published") is True:
				raise PermissionDenied("Teachers cannot publish finalized results.")
			result = serializer.save(entered_by=user)
			AuditLog.objects.create(actor=user, action="result.updated", model_name="Result", object_id=str(result.pk))
			return

		# Registrar/Admin may only toggle publishing state for validation/finalization.
		if user.role in ["registrar", "admin"]:
			allowed_fields = {"published"}
			provided_fields = set(serializer.validated_data.keys())
			if not provided_fields.issubset(allowed_fields):
				raise PermissionDenied("Registrar/Admin can only publish or unpublish results.")
			result = serializer.save()
			AuditLog.objects.create(actor=user, action="result.published_state_changed", model_name="Result", object_id=str(result.pk))
			return

		raise PermissionDenied("Not allowed to update results.")

	def perform_destroy(self, instance):
		user = self.request.user
		if user.role not in ["teacher", "admin"]:
			raise PermissionDenied("Only teacher or admin can delete results.")
		if user.role == "teacher" and instance.course.teacher_id != user.id:
			raise PermissionDenied("You can only delete results for your assigned courses.")
		instance.delete()

	@action(detail=True, methods=["post"])
	def submit(self, request, pk=None):
		result = self.get_object()
		if request.user.role != "teacher" or result.course.teacher_id != request.user.id:
			raise PermissionDenied("You can only submit results for your assigned courses.")
		result.is_draft = False
		result.save(update_fields=["is_draft"])
		AuditLog.objects.create(actor=request.user, action="result.submitted", model_name="Result", object_id=str(result.pk))
		return Response(ResultSerializer(result).data)

	@action(detail=True, methods=["post"])
	def publish(self, request, pk=None):
		result = self.get_object()
		if request.user.role not in ["registrar", "admin"]:
			raise PermissionDenied("Only registrar or admin can publish results.")
		if result.is_draft:
			raise PermissionDenied("Draft results cannot be published.")
		result.published = True
		result.save(update_fields=["published"])
		AuditLog.objects.create(actor=request.user, action="result.published", model_name="Result", object_id=str(result.pk))
		return Response(ResultSerializer(result).data)
