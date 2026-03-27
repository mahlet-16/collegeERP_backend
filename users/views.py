from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from .serializers import UserSerializer
from .serializers import UserCreateSerializer
from .serializers import UserManageSerializer
from .permissions import IsAdminOrRegistrar
from .models import User


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
	"""Allow only admin or registrar to create new user accounts.

	Registrars may not create admin accounts.
	"""

	permission_classes = [IsAdminOrRegistrar]

	def post(self, request):
		serializer = UserCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		# Prevent a registrar from creating admin accounts
		requested_role = serializer.validated_data.get("role")
		if request.user.role == User.Role.REGISTRAR and requested_role == User.Role.ADMIN:
			return Response({"detail": "Registrar cannot create admin accounts."}, status=status.HTTP_403_FORBIDDEN)

		user = serializer.save()
		return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserListView(ListAPIView):
	"""Allow admin/registrar to list users for management workflows."""

	permission_classes = [IsAdminOrRegistrar]
	serializer_class = UserSerializer
	queryset = User.objects.all().order_by("username")


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

		if instance.role == User.Role.ADMIN and request.data.get("is_active") is False:
			if request.user.role != User.Role.ADMIN:
				return Response({"detail": "Only admin can deactivate admin accounts."}, status=status.HTTP_403_FORBIDDEN)

		return super().update(request, *args, **kwargs)
