from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, DepartmentViewSet, EnrollmentViewSet, ProgramViewSet

router = DefaultRouter()
router.register("departments", DepartmentViewSet)
router.register("programs", ProgramViewSet)
router.register("items", CourseViewSet)
router.register("enrollments", EnrollmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
