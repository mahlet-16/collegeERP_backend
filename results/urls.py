from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ResultViewSet

router = DefaultRouter()
router.register("items", ResultViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
