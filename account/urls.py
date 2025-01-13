# account/urls.py
from django.urls import path
from .views import (
    UpdatePasswordView,
    UserDetailView,
    DeleteUserView,
    RegisterView,
    LoginView,
    LogoutView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path(
        "account/change-password/", UpdatePasswordView.as_view(), name="change-password"
    ),
    path("account/profile/", UserDetailView.as_view(), name="get-update-profile"),
    path("account/profie/delete/", DeleteUserView.as_view(), name="delete-profile"),
]
