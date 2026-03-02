from django.urls import path

from .views import MeView, UsersIndexView

urlpatterns = [
    path("", UsersIndexView.as_view(), name="users-index"),
    path("me", MeView.as_view(), name="me-no-slash"),
    path("me/", MeView.as_view(), name="me"),
]
