from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExamScheduleViewSet, TimetableEntryViewSet

router = DefaultRouter()
router.register("entries", TimetableEntryViewSet)
router.register("exams", ExamScheduleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
