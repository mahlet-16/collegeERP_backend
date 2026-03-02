from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


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
