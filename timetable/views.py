from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import AuditLog
from users.permissions import IsAdminOrRegistrar, IsRegistrar

from .models import ExamSchedule, TimetableEntry
from .serializers import ExamScheduleSerializer, TimetableEntrySerializer


class TimetableEntryViewSet(viewsets.ModelViewSet):
	queryset = TimetableEntry.objects.select_related("course", "assigned_by", "course__teacher").all()
	serializer_class = TimetableEntrySerializer
	filterset_fields = ["term", "day", "room", "course", "published"]
	search_fields = ["term", "day", "room", "course__code", "course__name", "course__teacher__username"]
	ordering_fields = ["term", "day", "start_time", "end_time", "room", "course__code", "published"]

	def get_queryset(self):
		queryset = super().get_queryset().order_by("day", "start_time")
		user = self.request.user
		if user.role == "student":
			return queryset.filter(published=True, course__enrollments__student=user).distinct()
		if user.role == "teacher":
			return queryset.filter(course__teacher=user, published=True)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsAdminOrRegistrar()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		entry = serializer.save(assigned_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="timetable.created",
			model_name="TimetableEntry",
			object_id=str(entry.pk),
			detail={"course": entry.course_id, "term": entry.term},
		)

	def perform_update(self, serializer):
		entry = serializer.save(assigned_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="timetable.updated",
			model_name="TimetableEntry",
			object_id=str(entry.pk),
		)

	@action(detail=True, methods=["post"], permission_classes=[IsAdminOrRegistrar])
	def publish(self, request, pk=None):
		entry = self.get_object()
		entry.published = True
		entry.assigned_by = request.user
		entry.save(update_fields=["published", "assigned_by"])
		AuditLog.objects.create(actor=request.user, action="timetable.published", model_name="TimetableEntry", object_id=str(entry.pk))
		return Response(TimetableEntrySerializer(entry).data)


class ExamScheduleViewSet(viewsets.ModelViewSet):
	queryset = ExamSchedule.objects.select_related("course", "scheduled_by", "course__teacher").all()
	serializer_class = ExamScheduleSerializer
	filterset_fields = ["term", "date", "room", "course", "published"]
	search_fields = ["term", "room", "course__code", "course__name", "course__teacher__username", "description"]
	ordering_fields = ["term", "date", "start_time", "end_time", "room", "course__code", "published"]

	def get_queryset(self):
		queryset = super().get_queryset().order_by("date", "start_time")
		user = self.request.user
		if user.role == "student":
			return queryset.filter(published=True, course__enrollments__student=user).distinct()
		if user.role == "teacher":
			return queryset.filter(course__teacher=user, published=True)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsAdminOrRegistrar()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		exam = serializer.save(scheduled_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="exam_schedule.created",
			model_name="ExamSchedule",
			object_id=str(exam.pk),
			detail={"course": exam.course_id, "term": exam.term, "date": str(exam.date)},
		)

	def perform_update(self, serializer):
		exam = serializer.save(scheduled_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="exam_schedule.updated",
			model_name="ExamSchedule",
			object_id=str(exam.pk),
		)

	@action(detail=True, methods=["post"], permission_classes=[IsAdminOrRegistrar])
	def publish(self, request, pk=None):
		exam = self.get_object()
		exam.published = True
		exam.scheduled_by = request.user
		exam.save(update_fields=["published", "scheduled_by"])
		AuditLog.objects.create(actor=request.user, action="exam_schedule.published", model_name="ExamSchedule", object_id=str(exam.pk))
		return Response(ExamScheduleSerializer(exam).data)
