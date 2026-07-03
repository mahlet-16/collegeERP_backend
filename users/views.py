import csv
import io

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework import viewsets
from rest_framework.decorators import action

from .serializers import UserSerializer
from .serializers import UserCreateSerializer
from .serializers import UserManageSerializer
from .serializers import (
	AuditLogSerializer,
	NotificationSerializer,
	StudentProfileSerializer,
	SystemSettingSerializer,
	TeacherProfileSerializer,
)
from .permissions import IsAdmin, IsAdminOrRegistrar
from .models import AuditLog, Notification, StudentProfile, SystemSetting, TeacherProfile, User


def write_audit(actor, action, instance=None, detail=None):
	AuditLog.objects.create(
		actor=actor if actor and actor.is_authenticated else None,
		action=action,
		model_name=instance.__class__.__name__ if instance else "",
		object_id=str(getattr(instance, "pk", "")) if instance else "",
		detail=detail or {},
	)


class UsersIndexView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		return Response(
			{
				"message": "Users API",
				"endpoints": {
					"me": "/api/users/me/",
					"token": "/api/token/",
					"token_refresh": "/api/token/refresh/",
				},
			}
		)


class MeView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		return Response(UserSerializer(request.user).data)


class CreateUserView(APIView):
	"""Allow only registrar to create student and teacher accounts.

	Only admins may create additional admins or registrars.
	"""

	permission_classes = [IsAdminOrRegistrar]

	def post(self, request):
		serializer = UserCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		requested_role = serializer.validated_data.get("role")
		if request.user.role == User.Role.REGISTRAR and requested_role not in [User.Role.STUDENT, User.Role.TEACHER]:
			return Response({"detail": "Registrar can only create student and teacher accounts."}, status=status.HTTP_403_FORBIDDEN)

		user = serializer.save()
		write_audit(request.user, "user.created", user, {"role": user.role})
		return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserListView(ListAPIView):
	"""Allow admin/registrar to list users for management workflows."""

	permission_classes = [IsAdminOrRegistrar]
	serializer_class = UserSerializer
	queryset = User.objects.all().order_by("username")
	filterset_fields = ["role", "is_active"]
	search_fields = ["username", "first_name", "last_name", "email", "phone"]
	ordering_fields = ["username", "role", "date_joined", "is_active"]


class UserManageView(RetrieveUpdateAPIView):
	"""Allow admin/registrar to edit user profile/role/status with guardrails.

	Registrars may not change a user to admin role and may not edit existing admins.
	Only admins may deactivate admin accounts.
	"""

	permission_classes = [IsAdminOrRegistrar]
	serializer_class = UserManageSerializer
	queryset = User.objects.all().order_by("id")

	def update(self, request, *args, **kwargs):
		instance = self.get_object()

		if request.user.role == User.Role.REGISTRAR:
			if instance.role == User.Role.ADMIN:
				return Response({"detail": "Registrar cannot modify admin accounts."}, status=status.HTTP_403_FORBIDDEN)
			requested_role = request.data.get("role", instance.role)
			if requested_role == User.Role.ADMIN:
				return Response({"detail": "Registrar cannot assign admin role."}, status=status.HTTP_403_FORBIDDEN)

		if instance.role == User.Role.ADMIN:
			is_active = request.data.get("is_active", None)
			if is_active is not None:
				is_active_value = str(is_active).lower() in ["false", "0", "no"]
				if is_active_value and request.user.role != User.Role.ADMIN:
					return Response({"detail": "Only admin can deactivate admin accounts."}, status=status.HTTP_403_FORBIDDEN)

		response = super().update(request, *args, **kwargs)
		write_audit(request.user, "user.updated", instance, request.data)
		return response


class BulkCreateUsersView(APIView):
	"""Create users from a CSV file with username,password,role columns."""

	permission_classes = [IsAdminOrRegistrar]
	parser_classes = [MultiPartParser]

	def post(self, request):
		upload = request.FILES.get("file")
		if not upload:
			return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

		reader = csv.DictReader(io.StringIO(upload.read().decode("utf-8-sig")))
		created = []
		errors = []
		for index, row in enumerate(reader, start=2):
			data = {
				"username": row.get("username", "").strip(),
				"password": row.get("password", "").strip(),
				"first_name": row.get("first_name", "").strip(),
				"last_name": row.get("last_name", "").strip(),
				"email": row.get("email", "").strip(),
				"phone": row.get("phone", "").strip(),
				"role": row.get("role", "student").strip() or "student",
			}
			if request.user.role == User.Role.REGISTRAR and data["role"] not in [User.Role.STUDENT, User.Role.TEACHER]:
				errors.append({"row": index, "detail": "Registrar can only create student and teacher accounts."})
				continue
			serializer = UserCreateSerializer(data=data)
			if serializer.is_valid():
				user = serializer.save()
				created.append(UserSerializer(user).data)
				write_audit(request.user, "user.bulk_created", user, {"row": index})
			else:
				errors.append({"row": index, "detail": serializer.errors})

		return Response({"created": created, "errors": errors}, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class MyProfileView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		if request.user.role == User.Role.STUDENT:
			profile, _ = StudentProfile.objects.get_or_create(user=request.user)
			return Response(StudentProfileSerializer(profile).data)
		if request.user.role == User.Role.TEACHER:
			profile, _ = TeacherProfile.objects.get_or_create(user=request.user)
			return Response(TeacherProfileSerializer(profile).data)
		return Response(UserSerializer(request.user).data)

	def patch(self, request):
		if request.user.role == User.Role.STUDENT:
			profile, _ = StudentProfile.objects.get_or_create(user=request.user)
			serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
		elif request.user.role == User.Role.TEACHER:
			profile, _ = TeacherProfile.objects.get_or_create(user=request.user)
			serializer = TeacherProfileSerializer(profile, data=request.data, partial=True)
		else:
			serializer = UserManageSerializer(request.user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		instance = serializer.save()
		write_audit(request.user, "profile.updated", instance, request.data)
		return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
	serializer_class = NotificationSerializer
	filterset_fields = ["recipient", "read"]
	search_fields = ["title", "message", "recipient__username"]
	ordering_fields = ["created_at", "read", "title"]

	def get_queryset(self):
		user = self.request.user
		if user.role == User.Role.ADMIN:
			return Notification.objects.select_related("recipient").all()
		return Notification.objects.filter(recipient=user)

	def get_permissions(self):
		if self.action in ["create", "destroy", "update", "partial_update"]:
			return [IsAdminOrRegistrar()]
		return [IsAuthenticated()]

	def perform_create(self, serializer):
		notification = serializer.save()
		write_audit(self.request.user, "notification.created", notification)

	@action(detail=True, methods=["post"])
	def mark_read(self, request, pk=None):
		notification = self.get_object()
		if notification.recipient != request.user and request.user.role != User.Role.ADMIN:
			return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
		notification.read = True
		notification.save(update_fields=["read"])
		return Response(NotificationSerializer(notification).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
	permission_classes = [IsAdmin]
	serializer_class = AuditLogSerializer
	queryset = AuditLog.objects.select_related("actor").all()
	filterset_fields = ["actor", "action", "model_name"]
	search_fields = ["action", "model_name", "object_id", "actor__username"]
	ordering_fields = ["created_at", "action", "model_name"]


class SystemSettingViewSet(viewsets.ModelViewSet):
	permission_classes = [IsAdmin]
	serializer_class = SystemSettingSerializer
	queryset = SystemSetting.objects.select_related("updated_by").all().order_by("key")
	lookup_field = "key"
	filterset_fields = ["key"]
	search_fields = ["key"]
	ordering_fields = ["key", "updated_at"]

	def perform_create(self, serializer):
		setting = serializer.save(updated_by=self.request.user)
		write_audit(self.request.user, "setting.created", setting, serializer.validated_data)

	def perform_update(self, serializer):
		setting = serializer.save(updated_by=self.request.user)
		write_audit(self.request.user, "setting.updated", setting, serializer.validated_data)
