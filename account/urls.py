# account/urls.py
from django.urls import path
from .views import (
    UserRegistrationView,
    LoginView,
    LogoutView,
    UpdatePasswordView,
    UserDetailView,
    DeleteUserView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("change-password/", UpdatePasswordView.as_view(), name="change-password"),
    path("profile/", UserDetailView.as_view(), name="get-update-profile"),
    path("profie/delete/", DeleteUserView.as_view(), name="delete-profile"),
]
