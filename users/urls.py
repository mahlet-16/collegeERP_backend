from django.urls import path

from .views import MeView, UsersIndexView, CreateUserView, UserListView, UserManageView

urlpatterns = [
    path("", UsersIndexView.as_view(), name="users-index"),
    path("list/", UserListView.as_view(), name="users-list"),
    path("manage/<int:pk>/", UserManageView.as_view(), name="users-manage"),
    path("me", MeView.as_view(), name="me-no-slash"),
    path("me/", MeView.as_view(), name="me"),
    path("create/", CreateUserView.as_view(), name="user-create"),
]
