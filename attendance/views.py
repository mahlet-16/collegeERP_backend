from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from users.models import AuditLog
from users.permissions import IsTeacher

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
	queryset = Attendance.objects.select_related("student", "course", "course__section", "recorded_by").all()
	serializer_class = AttendanceSerializer
	filterset_fields = ["student", "course", "date", "status", "is_draft"]
	search_fields = ["student__username", "course__code", "course__name", "course__section__name", "status", "comment"]
	ordering_fields = ["date", "status", "course__code", "course__section__name", "student__username"]

	def get_queryset(self):
		queryset = super().get_queryset().order_by("-date")
		user = self.request.user
		section_id = self.request.query_params.get("section")
		if section_id and user.role in ["admin", "registrar"]:
			queryset = queryset.filter(course__section_id=section_id)
		if user.role == "student":
			return queryset.filter(student=user, is_draft=False)
		if user.role == "teacher":
			return queryset.filter(course__teacher=user)
		return queryset

	def get_permissions(self):
		if self.action in ["create", "update", "partial_update", "destroy"]:
			return [IsTeacher()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		attendance = serializer.save(recorded_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="attendance.created",
			model_name="Attendance",
			object_id=str(attendance.pk),
			detail={"course": attendance.course_id, "student": attendance.student_id, "draft": attendance.is_draft},
		)

	def perform_update(self, serializer):
		attendance = serializer.save(recorded_by=self.request.user)
		AuditLog.objects.create(
			actor=self.request.user,
			action="attendance.updated",
			model_name="Attendance",
			object_id=str(attendance.pk),
			detail={"draft": attendance.is_draft},
		)

	def perform_destroy(self, instance):
		AuditLog.objects.create(
			actor=self.request.user,
			action="attendance.deleted",
			model_name="Attendance",
			object_id=str(instance.pk),
			detail={"course": instance.course_id, "student": instance.student_id, "date": str(instance.date)},
		)
		instance.delete()

	@action(detail=False, methods=["post"])
	def bulk(self, request):
		if request.user.role != "teacher":
			return Response({"detail": "Only teachers can record attendance."}, status=status.HTTP_403_FORBIDDEN)

		records = request.data.get("records", [])
		if not isinstance(records, list) or not records:
			return Response({"detail": "records must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

		created = []
		errors = []
		for index, record in enumerate(records):
			serializer = self.get_serializer(data=record)
			if serializer.is_valid():
				attendance = serializer.save(recorded_by=request.user)
				created.append(attendance)
				AuditLog.objects.create(
					actor=request.user,
					action="attendance.bulk_created",
					model_name="Attendance",
					object_id=str(attendance.pk),
					detail={"course": attendance.course_id, "student": attendance.student_id, "draft": attendance.is_draft},
				)
			else:
				errors.append({"index": index, "detail": serializer.errors})

		return Response(
			{"created": AttendanceSerializer(created, many=True).data, "errors": errors},
			status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
		)

	@action(detail=False, methods=["get"])
	def summary(self, request):
		queryset = self.get_queryset().filter(is_draft=False)
		student_id = request.query_params.get("student")
		course_id = request.query_params.get("course")
		if student_id and request.user.role in ["admin", "registrar", "teacher"]:
			queryset = queryset.filter(student_id=student_id)
		if course_id:
			queryset = queryset.filter(course_id=course_id)

		attended_statuses = [
			Attendance.Status.PRESENT,
			Attendance.Status.LATE,
			Attendance.Status.EXCUSED,
		]
		rows = (
			queryset.values("course", "course__code", "course__name")
			.annotate(
				total=Count("id"),
				attended=Count("id", filter=Q(status__in=attended_statuses)),
				absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
			)
			.order_by("course__code")
		)
		summary = []
		for row in rows:
			total = row["total"]
			percentage = round((row["attended"] / total) * 100, 2) if total else 0
			summary.append(
				{
					"course": row["course"],
					"course_code": row["course__code"],
					"course_name": row["course__name"],
					"total": total,
					"attended": row["attended"],
					"absent": row["absent"],
					"attendance_percentage": percentage,
					"meets_75_percent_requirement": percentage >= 75,
				}
			)
		return Response(summary)
