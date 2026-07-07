from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicYearViewSet,
    ClassroomViewSet,
    CollegeViewSet,
    CourseViewSet,
    DepartmentViewSet,
    EnrollmentViewSet,
    ProgramViewSet,
    SectionViewSet,
    SemesterViewSet,
)

router = DefaultRouter()
router.register("colleges", CollegeViewSet)
router.register("departments", DepartmentViewSet)
router.register("programs", ProgramViewSet)
router.register("academic-years", AcademicYearViewSet)
router.register("semesters", SemesterViewSet)
router.register("sections", SectionViewSet, basename="section")
router.register("classrooms", ClassroomViewSet)
router.register("items", CourseViewSet)
router.register("enrollments", EnrollmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
