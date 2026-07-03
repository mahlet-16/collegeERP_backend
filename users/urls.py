from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    BulkCreateUsersView,
    CreateUserView,
    MeView,
    MyProfileView,
    NotificationViewSet,
    SystemSettingViewSet,
    UserListView,
    UserManageView,
    UsersIndexView,
)

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("settings", SystemSettingViewSet, basename="system-setting")

urlpatterns = [
    path("", UsersIndexView.as_view(), name="users-index"),
    path("list/", UserListView.as_view(), name="users-list"),
    path("manage/<int:pk>/", UserManageView.as_view(), name="users-manage"),
    path("me", MeView.as_view(), name="me-no-slash"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", MyProfileView.as_view(), name="my-profile"),
    path("create/", CreateUserView.as_view(), name="user-create"),
    path("bulk-create/", BulkCreateUsersView.as_view(), name="user-bulk-create"),
    path("", include(router.urls)),
]
