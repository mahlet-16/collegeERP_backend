from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import UserSerializer
from .serializers import UserCreateSerializer
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
